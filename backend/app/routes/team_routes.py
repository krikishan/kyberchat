from flask import Blueprint, g, jsonify

from app.auth.tokens import require_auth
from app.database.db import get_db

team_bp = Blueprint("team", __name__)


@team_bp.route("/members", methods=["GET"])
@require_auth
def list_team_members():
    """Any authenticated user can see basic directory info for active
    members — needed to start a conversation or add someone to a group.
    Deliberately excludes email, status, and anything admin-only."""
    db = get_db()
    current_user_id = str(g.current_user["_id"])
    members = db.users.find({"status": "active"}, {"name": 1, "username": 1, "role": 1, "team_id": 1, "team_name": 1})
    return jsonify({
        "members": [
            {
                "id": str(m["_id"]),
                "name": m["name"],
                "username": m["username"],
                "role": m["role"],
                "team_id": m.get("team_id"),
                "team_name": m.get("team_name"),
            }
            for m in members if str(m["_id"]) != current_user_id
        ]
    })
