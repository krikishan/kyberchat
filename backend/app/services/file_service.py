import datetime

from bson import Binary

from app.crypto import session_manager
from app.services.conversation_service import ConversationError, require_participant
from app.services.group_service import GroupError, require_member
from app.utils.file_validation import FileValidationError, validate_and_prepare


class FileServiceError(Exception):
    def __init__(self, message: str, code: str = "error"):
        super().__init__(message)
        self.code = code


def _resolve_context(db, context_type: str, context_id: str, user_id: str):
    if context_type == "conversation":
        conversation = db.conversations.find_one({"conversation_id": context_id})
        if not conversation:
            raise FileServiceError("Conversation not found.", "not_found")
        try:
            require_participant(conversation, user_id)
        except ConversationError as exc:
            raise FileServiceError(str(exc), "unauthorized") from exc
    elif context_type == "group":
        group = db.groups.find_one({"group_id": context_id})
        if not group:
            raise FileServiceError("Group not found.", "not_found")
        try:
            require_member(group, user_id)
        except GroupError as exc:
            raise FileServiceError(str(exc), "unauthorized") from exc
    else:
        raise FileServiceError("Invalid context_type.", "invalid_context")


def upload_file(db, app_secret_key: str, uploader_id: str, context_type: str, context_id: str,
                 filename: str, declared_mime_type: str | None, file_bytes: bytes) -> dict:
    _resolve_context(db, context_type, context_id, uploader_id)

    try:
        prepared = validate_and_prepare(filename, file_bytes, declared_mime_type)
    except FileValidationError as exc:
        raise FileServiceError(str(exc), exc.code) from exc

    encrypted = session_manager.encrypt_for_context(db, app_secret_key, context_type, context_id, uploader_id, file_bytes)

    now = datetime.datetime.utcnow()
    doc = {
        "file_id": prepared["storage_id"],
        "original_filename": prepared["original_filename"],
        "size": prepared["size"],
        "mime_type": prepared["mime_type"],
        "sender_id": uploader_id,
        "context_type": context_type,
        "context_id": context_id,
        "storage_reference": f"mongo:files:{prepared['storage_id']}",
        "ciphertext": Binary(bytes.fromhex(encrypted["ciphertext"])),
        "nonce": encrypted["nonce"],
        "key_version": encrypted["key_version"],
        "algorithm": encrypted["algorithm"],
        "created_at": now,
    }
    db.files.insert_one(doc)
    return {k: v for k, v in doc.items() if k not in ("ciphertext",)}


def get_file_metadata(db, file_id: str, requesting_user_id: str) -> dict:
    file_doc = db.files.find_one({"file_id": file_id})
    if not file_doc:
        raise FileServiceError("File not found.", "not_found")
    _resolve_context(db, file_doc["context_type"], file_doc["context_id"], requesting_user_id)
    return {k: v for k, v in file_doc.items() if k not in ("ciphertext", "_id")}


def download_file(db, app_secret_key: str, file_id: str, requesting_user_id: str) -> tuple[bytes, dict]:
    file_doc = db.files.find_one({"file_id": file_id})
    if not file_doc:
        raise FileServiceError("File not found.", "not_found")
    _resolve_context(db, file_doc["context_type"], file_doc["context_id"], requesting_user_id)

    ciphertext_hex = bytes(file_doc["ciphertext"]).hex()
    plaintext = session_manager.decrypt_for_context(
        db, app_secret_key, file_doc["context_type"], file_doc["context_id"], requesting_user_id,
        ciphertext_hex, file_doc["nonce"], file_doc["key_version"],
    )
    metadata = {k: v for k, v in file_doc.items() if k not in ("ciphertext", "_id")}
    return plaintext, metadata


def list_files(db, context_type: str, context_id: str, requesting_user_id: str) -> list[dict]:
    _resolve_context(db, context_type, context_id, requesting_user_id)
    files = db.files.find({"context_type": context_type, "context_id": context_id}, {"ciphertext": 0})
    return [
        {
            "file_id": f["file_id"], "original_filename": f["original_filename"],
            "size": f["size"], "mime_type": f["mime_type"], "sender_id": f["sender_id"],
            "created_at": f["created_at"].isoformat(),
        }
        for f in files
    ]
