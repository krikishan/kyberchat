import io
import json

from flask import Blueprint, Response, current_app, g, jsonify, request

from app import limiter
from app.auth.tokens import require_auth
from app.database.db import get_db
from app.services.file_service import FileServiceError, download_file, get_file_metadata, list_files, upload_file

file_bp = Blueprint("files", __name__)


def _status_for(code: str) -> int:
    return {"not_found": 404, "unauthorized": 403}.get(code, 400)


@file_bp.route("", methods=["POST"])
@require_auth
@limiter.limit("20 per minute")
def upload():
    """multipart/form-data: file=<binary>, context_type=conversation|group, context_id=<id>
    After successful upload, a 'file' message is inserted into the conversation/group
    message history so the attachment appears inline in the chat."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400
    context_type = request.form.get("context_type")
    context_id = request.form.get("context_id")
    if not context_type or not context_id:
        return jsonify({"error": "context_type and context_id are required."}), 400

    uploaded = request.files["file"]
    file_bytes = uploaded.read()

    db = get_db()
    user_id = str(g.current_user["_id"])
    try:
        result = upload_file(
            db, current_app.config["SECRET_KEY"], user_id,
            context_type, context_id, uploaded.filename, uploaded.content_type, file_bytes,
        )
    except FileServiceError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), _status_for(exc.code)

    # Create a file-type message so the attachment appears in chat history.
    file_meta_payload = json.dumps({
        "file_id": result["file_id"],
        "filename": result["original_filename"],
        "size": result["size"],
        "mime_type": result["mime_type"],
    })
    try:
        from app.services.conversation_service import send_message as send_conv_msg
        from app.services.group_service import send_message as send_group_msg

        if context_type == "conversation":
            msg = send_conv_msg(db, current_app.config["SECRET_KEY"], context_id, user_id, file_meta_payload, message_type="file")
        elif context_type == "group":
            msg = send_group_msg(db, current_app.config["SECRET_KEY"], context_id, user_id, file_meta_payload, message_type="file")
    except Exception as exc:
        current_app.logger.warning("Failed to insert inline file message: %s", exc)

    return jsonify({
        "file_id": result["file_id"],
        "original_filename": result["original_filename"],
        "size": result["size"],
        "mime_type": result["mime_type"],
        "created_at": result["created_at"].isoformat(),
    }), 201


@file_bp.route("", methods=["GET"])
@require_auth
def list_context_files():
    context_type = request.args.get("context_type")
    context_id = request.args.get("context_id")
    if not context_type or not context_id:
        return jsonify({"error": "context_type and context_id query params are required."}), 400
    db = get_db()
    try:
        files = list_files(db, context_type, context_id, str(g.current_user["_id"]))
    except FileServiceError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), _status_for(exc.code)
    return jsonify({"files": files})


@file_bp.route("/<file_id>", methods=["GET"])
@require_auth
def metadata(file_id):
    db = get_db()
    try:
        meta = get_file_metadata(db, file_id, str(g.current_user["_id"]))
    except FileServiceError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), _status_for(exc.code)
    return jsonify({
        "file_id": meta["file_id"], "original_filename": meta["original_filename"],
        "size": meta["size"], "mime_type": meta["mime_type"], "sender_id": meta["sender_id"],
        "created_at": meta["created_at"].isoformat(),
    })


@file_bp.route("/<file_id>/download", methods=["GET"])
@require_auth
@limiter.limit("60 per minute")
def download(file_id):
    db = get_db()
    try:
        plaintext, meta = download_file(db, current_app.config["SECRET_KEY"], file_id, str(g.current_user["_id"]))
    except FileServiceError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), _status_for(exc.code)

    # Safe headers — never trust a client-provided path; filename is quoted/sanitized already.
    response = Response(io.BytesIO(plaintext).read(), mimetype=meta["mime_type"])
    response.headers["Content-Disposition"] = f'attachment; filename="{meta["original_filename"]}"'
    return response
