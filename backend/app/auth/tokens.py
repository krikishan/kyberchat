import datetime
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request


def issue_token(user_id: str, role: str, session_version: int) -> str:
    now = datetime.datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": role,
        "sv": session_version,  # bumped on password change -> invalidates old tokens
        "iat": now,
        "exp": now + datetime.timedelta(minutes=current_app.config["JWT_ACCESS_TOKEN_EXPIRES_MIN"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])


def _extract_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]
    return None


def require_auth(f):
    """Verifies the JWT, checks it against the user's current session_version
    (so password changes / logout invalidate old tokens), and attaches the
    user to flask.g.current_user. Never trusts a client-asserted role."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Authentication required."}), 401
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid session."}), 401

        from app.database.db import get_db
        from bson import ObjectId

        db = get_db()
        user = db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user or user.get("status") != "active":
            return jsonify({"error": "Account not available."}), 401
        if user.get("session_version", 0) != payload.get("sv"):
            return jsonify({"error": "Session expired. Please log in again."}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return wrapper


ROLE_HIERARCHY = {"developer": 3, "admin": 2, "user": 1}


def require_role(minimum_role: str):
    """Checks that the authenticated user's role is at or above the
    specified level.  Hierarchy: developer > admin > user.
    A developer can access admin-restricted endpoints automatically."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user:
                return jsonify({"error": "Authentication required."}), 401
            user_level = ROLE_HIERARCHY.get(user.get("role"), 0)
            required_level = ROLE_HIERARCHY.get(minimum_role, 0)
            if user_level < required_level:
                return jsonify({"error": "You are not authorized to perform this action."}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
