from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify, request

from app import limiter
from app.auth.tokens import require_auth
from app.database.db import get_db
from app.services.conversation_service import ConversationError, get_or_create_conversation, list_messages, send_message

conversation_bp = Blueprint("conversations", __name__)


@conversation_bp.route("", methods=["POST"])
@require_auth
def create_conversation():
    data = request.get_json(silent=True) or {}
    other_user_id = data.get("user_id")
    if not other_user_id:
        return jsonify({"error": "user_id is required."}), 400

    db = get_db()
    try:
        conversation = get_or_create_conversation(db, current_app.config["SECRET_KEY"], str(g.current_user["_id"]), other_user_id)
    except ConversationError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), 400

    u = None
    try:
        u = db.users.find_one({"_id": ObjectId(other_user_id)}, {"name": 1, "username": 1, "role": 1})
    except Exception:
        pass
    if not u:
        u = db.users.find_one({"_id": other_user_id}, {"name": 1, "username": 1, "role": 1})

    other_name = (u.get("name") or u.get("username") or "Secure Contact") if u else "Secure Contact"
    other_uname = u.get("username", "") if u else ""

    return jsonify({
        "conversation_id": conversation["conversation_id"],
        "participants": conversation["participants"],
        "other_user_id": other_user_id,
        "other_user_name": other_name,
        "other_username": other_uname,
    }), 201


@conversation_bp.route("", methods=["GET"])
@require_auth
def list_conversations():
    db = get_db()
    user_id = str(g.current_user["_id"])
    convs = list(db.conversations.find({"participants": user_id}).sort("last_activity_at", -1))

    # Collect other user IDs
    other_uids = set()
    for c in convs:
        for p in c.get("participants", []):
            if p != user_id:
                other_uids.add(p)

    user_info = {}
    for uid in other_uids:
        u = None
        try:
            u = db.users.find_one({"_id": ObjectId(uid)}, {"name": 1, "username": 1, "role": 1})
        except Exception:
            pass
        if not u:
            u = db.users.find_one({"_id": uid}, {"name": 1, "username": 1, "role": 1})
        if u:
            user_info[uid] = {
                "name": u.get("name") or u.get("username") or "Secure Contact",
                "username": u.get("username") or "",
                "role": u.get("role") or "user",
            }

    results = []
    for c in convs:
        other_id = next((p for p in c.get("participants", []) if p != user_id), None)
        info = user_info.get(other_id, {})
        results.append({
            "conversation_id": c["conversation_id"],
            "participants": c.get("participants", []),
            "other_user_id": other_id,
            "other_user_name": info.get("name") or "Secure Contact",
            "other_username": info.get("username") or "",
            "other_user_role": info.get("role") or "user",
            "last_activity_at": c["last_activity_at"].isoformat(),
        })

    return jsonify({"conversations": results})


@conversation_bp.route("/<conversation_id>/messages", methods=["POST"])
@require_auth
@limiter.limit("60 per minute")
def post_message(conversation_id):
    data = request.get_json(silent=True) or {}
    content = data.get("content", "")
    if not content or len(content) > 5000:
        return jsonify({"error": "Message content must be 1-5000 characters."}), 400

    db = get_db()
    try:
        msg = send_message(db, current_app.config["SECRET_KEY"], conversation_id, str(g.current_user["_id"]), content)
    except ConversationError as exc:
        status = 404 if exc.code == "not_found" else 403
        return jsonify({"error": str(exc), "code": exc.code}), status

    return jsonify({
        "message_id": msg["message_id"],
        "timestamp": msg["timestamp"].isoformat(),
        "key_version": msg["key_version"],
    }), 201


@conversation_bp.route("/<conversation_id>/messages", methods=["GET"])
@require_auth
def get_messages(conversation_id):
    db = get_db()
    try:
        messages = list_messages(db, current_app.config["SECRET_KEY"], conversation_id, str(g.current_user["_id"]))
    except ConversationError as exc:
        status = 404 if exc.code == "not_found" else 403
        return jsonify({"error": str(exc), "code": exc.code}), status
    return jsonify({"messages": messages})
