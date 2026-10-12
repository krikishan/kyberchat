import datetime

from bson import ObjectId
from flask import Blueprint, g, jsonify, request

from app import limiter
from app.auth.passwords import validate_password_strength, verify_password, hash_password
from app.auth.tokens import issue_token, require_auth
from app.database.db import get_db
from app.services.audit_log import record_event

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    username_or_email = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not username_or_email or not password:
        return jsonify({"error": "Invalid username or password."}), 400

    db = get_db()
    user = db.users.find_one({
        "$or": [{"username": username_or_email}, {"email": username_or_email}]
    })

    # Generic error regardless of which check failed — never reveal existence.
    generic_error = jsonify({"error": "Invalid username or password."}), 401
    if not user or user.get("status") != "active":
        return generic_error
    if not verify_password(password, user["password_hash"]):
        record_event(db, event_type="login_failure", user_id=str(user["_id"]))
        return generic_error

    token = issue_token(str(user["_id"]), user["role"], user.get("session_version", 0))
    db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.datetime.utcnow()}})
    record_event(db, event_type="login_success", user_id=str(user["_id"]))

    return jsonify({
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "name": user["name"],
            "role": user["role"],
            "must_change_password": user.get("must_change_password", False),
        },
    })


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    db = get_db()
    # Bump session_version so this and any other outstanding tokens are invalidated.
    db.users.update_one({"_id": g.current_user["_id"]}, {"$inc": {"session_version": 1}})
    record_event(db, event_type="logout", user_id=str(g.current_user["_id"]))
    return jsonify({"message": "Logged out."})


@auth_bp.route("/change-password", methods=["POST"])
@require_auth
@limiter.limit("5 per minute")
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    user = g.current_user
    if not verify_password(current_password, user["password_hash"]):
        return jsonify({"error": "Current password is incorrect."}), 400

    valid, message = validate_password_strength(new_password)
    if not valid:
        return jsonify({"error": message}), 400

    db = get_db()
    db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": hash_password(new_password),
                "must_change_password": False,
                "updated_at": datetime.datetime.utcnow(),
            },
            "$inc": {"session_version": 1},  # invalidate old sessions
        },
    )
    record_event(db, event_type="password_changed", user_id=str(user["_id"]))
    # Issue a fresh token under the new session_version so the caller stays logged in.
    new_token = issue_token(str(user["_id"]), user["role"], user.get("session_version", 0) + 1)
    return jsonify({"message": "Password updated.", "token": new_token})


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    user = g.current_user
    return jsonify({
        "id": str(user["_id"]),
        "username": user["username"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "team_id": user.get("team_id"),
        "team_name": user.get("team_name"),
        "must_change_password": user.get("must_change_password", False),
    })
