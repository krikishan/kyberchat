import datetime
import uuid

from app.crypto import session_manager


class ConversationError(Exception):
    def __init__(self, message: str, code: str = "error"):
        super().__init__(message)
        self.code = code


def get_or_create_conversation(db, app_secret_key: str, user_a: str, user_b: str) -> dict:
    if user_a == user_b:
        raise ConversationError("Cannot start a conversation with yourself.", "invalid_participants")

    participants = sorted([user_a, user_b])
    existing = db.conversations.find_one({"participants": participants})
    if existing:
        return existing

    now = datetime.datetime.utcnow()
    conversation_id = str(uuid.uuid4())
    session_manager.establish_session(db, app_secret_key, "conversation", conversation_id, participants)

    doc = {
        "conversation_id": conversation_id,
        "participants": participants,
        "created_at": now,
        "last_activity_at": now,
    }
    db.conversations.insert_one(doc)
    return doc


def require_participant(conversation: dict, user_id: str) -> None:
    if user_id not in conversation.get("participants", []):
        raise ConversationError("You are not authorized to access this conversation.", "unauthorized")


def send_message(db, app_secret_key: str, conversation_id: str, sender_id: str, plaintext: str, message_type: str = "text") -> dict:
    conversation = db.conversations.find_one({"conversation_id": conversation_id})
    if not conversation:
        raise ConversationError("Conversation not found.", "not_found")
    require_participant(conversation, sender_id)

    encrypted = session_manager.encrypt_for_context(
        db, app_secret_key, "conversation", conversation_id, sender_id, plaintext.encode("utf-8")
    )
    message_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow()
    doc = {
        "message_id": message_id,
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "message_type": message_type,
        "ciphertext": encrypted["ciphertext"],
        "nonce": encrypted["nonce"],
        "key_version": encrypted["key_version"],
        "algorithm": encrypted["algorithm"],
        "timestamp": now,  # server-generated — never trust a client timestamp
    }
    db.messages.insert_one(doc)
    db.conversations.update_one({"conversation_id": conversation_id}, {"$set": {"last_activity_at": now}})
    return doc


def list_messages(db, app_secret_key: str, conversation_id: str, requesting_user_id: str) -> list[dict]:
    conversation = db.conversations.find_one({"conversation_id": conversation_id})
    if not conversation:
        raise ConversationError("Conversation not found.", "not_found")
    require_participant(conversation, requesting_user_id)

    results = []
    for msg in db.messages.find({"conversation_id": conversation_id}).sort("timestamp", 1):
        plaintext = session_manager.decrypt_for_context(
            db, app_secret_key, "conversation", conversation_id, requesting_user_id,
            msg["ciphertext"], msg["nonce"], msg["key_version"],
        )
        results.append({
            "message_id": msg["message_id"],
            "sender_id": msg["sender_id"],
            "content": plaintext.decode("utf-8"),
            "timestamp": msg["timestamp"].isoformat(),
            "message_type": msg.get("message_type", "text"),
        })
    return results
