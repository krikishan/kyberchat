from flask import Blueprint, current_app, g, jsonify, request

from app import limiter
from app.auth.tokens import require_auth
from app.database.db import get_db
from app.services.group_service import (
    GroupError, add_member, create_group, list_messages, remove_member, require_member, send_message,
)

group_bp = Blueprint("groups", __name__)


def _status_for(code: str) -> int:
    return {"not_found": 404, "unauthorized": 403}.get(code, 400)


@group_bp.route("", methods=["POST"])
@require_auth
def create():
    data = request.get_json(silent=True) or {}
    db = get_db()
    try:
        group = create_group(db, current_app.config["SECRET_KEY"], str(g.current_user["_id"]),
                              data.get("group_name"), data.get("member_ids", []))
    except GroupError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), 400
    return jsonify({"group_id": group["group_id"], "group_name": group["group_name"], "members": group["members"]}), 201


@group_bp.route("", methods=["GET"])
@require_auth
def list_groups():
    db = get_db()
    user_id = str(g.current_user["_id"])
    groups = db.groups.find({"members": user_id}).sort("updated_at", -1)
    return jsonify({"groups": [
        {"group_id": grp["group_id"], "group_name": grp["group_name"], "members": grp["members"],
         "creator_id": grp["creator_id"]}
        for grp in groups
    ]})


@group_bp.route("/<group_id>", methods=["GET"])
@require_auth
def get_group(group_id):
    db = get_db()
    group = db.groups.find_one({"group_id": group_id})
    if not group:
        return jsonify({"error": "Group not found."}), 404
    try:
        require_member(group, str(g.current_user["_id"]))
    except GroupError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), 403
    return jsonify({"group_id": group["group_id"], "group_name": group["group_name"],
                     "members": group["members"], "creator_id": group["creator_id"]})


@group_bp.route("/<group_id>/members", methods=["POST"])
@require_auth
@limiter.limit("20 per minute")
def add_group_member(group_id):
    data = request.get_json(silent=True) or {}
    new_member_id = data.get("user_id")
    if not new_member_id:
        return jsonify({"error": "user_id is required."}), 400
    db = get_db()
    try:
        group = add_member(db, current_app.config["SECRET_KEY"], group_id, str(g.current_user["_id"]), new_member_id)
    except GroupError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), _status_for(exc.code)
    return jsonify({"members": group["members"]})


@group_bp.route("/<group_id>/members/<user_id>", methods=["DELETE"])
@require_auth
@limiter.limit("20 per minute")
def remove_group_member(group_id, user_id):
    db = get_db()
    try:
        group = remove_member(db, current_app.config["SECRET_KEY"], group_id, str(g.current_user["_id"]), user_id)
    except GroupError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), _status_for(exc.code)
    return jsonify({"members": group["members"]})


@group_bp.route("/<group_id>/messages", methods=["POST"])
@require_auth
@limiter.limit("60 per minute")
def post_message(group_id):
    data = request.get_json(silent=True) or {}
    content = data.get("content", "")
    if not content or len(content) > 5000:
        return jsonify({"error": "Message content must be 1-5000 characters."}), 400
    db = get_db()
    try:
        msg = send_message(db, current_app.config["SECRET_KEY"], group_id, str(g.current_user["_id"]), content)
    except GroupError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), _status_for(exc.code)
    return jsonify({"message_id": msg["message_id"], "timestamp": msg["timestamp"].isoformat(),
                     "key_version": msg["key_version"]}), 201


@group_bp.route("/<group_id>/messages", methods=["GET"])
@require_auth
def get_messages(group_id):
    db = get_db()
    try:
        messages = list_messages(db, current_app.config["SECRET_KEY"], group_id, str(g.current_user["_id"]))
    except GroupError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), _status_for(exc.code)
    return jsonify({"messages": messages})
