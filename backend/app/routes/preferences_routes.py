"""
Personal preferences: custom contact names and group names.
Each user can rename contacts and groups for their own view without
affecting other users or the official names.
"""
from flask import Blueprint, g, jsonify, request

from app.auth.tokens import require_auth
from app.database.db import get_db

preferences_bp = Blueprint("preferences", __name__)


@preferences_bp.route("", methods=["GET"])
@require_auth
def get_preferences():
    """Return the current user's custom contact and group names."""
    db = get_db()
    user_id = str(g.current_user["_id"])
    doc = db.user_preferences.find_one({"owner_id": user_id}) or {}
    return jsonify({
        "contact_names": doc.get("contact_names", {}),
        "group_names": doc.get("group_names", {}),
    })


@preferences_bp.route("/contacts/<contact_id>", methods=["PUT"])
@require_auth
def set_contact_name(contact_id):
    """Set a personal name for a contact. Body: {"name": "College Friend"}"""
    data = request.get_json(silent=True) or {}
    custom_name = (data.get("name") or "").strip()
    if not custom_name or len(custom_name) > 100:
        return jsonify({"error": "Name must be 1-100 characters."}), 400

    db = get_db()
    user_id = str(g.current_user["_id"])

    # Verify the contact exists
    from bson import ObjectId
    try:
        target = db.users.find_one({"_id": ObjectId(contact_id), "status": "active"})
    except Exception:
        return jsonify({"error": "Invalid contact id."}), 400
    if not target:
        return jsonify({"error": "Contact not found."}), 404

    db.user_preferences.update_one(
        {"owner_id": user_id},
        {"$set": {f"contact_names.{contact_id}": custom_name}},
        upsert=True,
    )
    return jsonify({"message": "Contact name updated.", "contact_id": contact_id, "name": custom_name})


@preferences_bp.route("/contacts/<contact_id>", methods=["DELETE"])
@require_auth
def remove_contact_name(contact_id):
    """Remove a personal contact name (fall back to official name)."""
    db = get_db()
    user_id = str(g.current_user["_id"])
    db.user_preferences.update_one(
        {"owner_id": user_id},
        {"$unset": {f"contact_names.{contact_id}": ""}},
    )
    return jsonify({"message": "Contact name removed."})


@preferences_bp.route("/groups/<group_id>", methods=["PUT"])
@require_auth
def set_group_name(group_id):
    """Set a personal name for a group. Body: {"name": "Final Year Team"}"""
    data = request.get_json(silent=True) or {}
    custom_name = (data.get("name") or "").strip()
    if not custom_name or len(custom_name) > 100:
        return jsonify({"error": "Name must be 1-100 characters."}), 400

    db = get_db()
    user_id = str(g.current_user["_id"])

    # Verify group exists and user is a member
    group = db.groups.find_one({"group_id": group_id})
    if not group:
        return jsonify({"error": "Group not found."}), 404
    if user_id not in group.get("members", []):
        return jsonify({"error": "You are not a member of this group."}), 403

    db.user_preferences.update_one(
        {"owner_id": user_id},
        {"$set": {f"group_names.{group_id}": custom_name}},
        upsert=True,
    )
    return jsonify({"message": "Group name updated.", "group_id": group_id, "name": custom_name})


@preferences_bp.route("/groups/<group_id>", methods=["DELETE"])
@require_auth
def remove_group_name(group_id):
    """Remove a personal group name (fall back to official name)."""
    db = get_db()
    user_id = str(g.current_user["_id"])
    db.user_preferences.update_one(
        {"owner_id": user_id},
        {"$unset": {f"group_names.{group_id}": ""}},
    )
    return jsonify({"message": "Group name removed."})
