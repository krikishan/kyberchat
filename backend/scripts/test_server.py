"""
Spins up the REAL Flask app (real routes, real crypto, real auth) backed by
mongomock instead of Atlas, on a real TCP port, so the actual frontend
code (src/api/client.js, real fetch calls) can be exercised against it in
integration tests — not just mocked.

Usage: python3 scripts/test_server.py [port]
Seeds:
  admin / AdminPass123!   (role: admin)
  alice / AlicePass123!   (role: user)
  bob   / BobPass123!     (role: user)
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SECRET_KEY", "integration-test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "integration-test-jwt-secret-key")
os.environ.setdefault("MONGODB_URI", "mongodb://unused")
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")

import mongomock

from app import create_app
from app.auth.passwords import hash_password
from app.crypto.key_directory import generate_and_store_user_keys


def seed(db, secret_key):
    now = datetime.datetime.utcnow()

    def make(name, email, username, password, role):
        result = db.users.insert_one({
            "name": name, "email": email, "username": username,
            "password_hash": hash_password(password), "role": role,
            "status": "active", "must_change_password": False,
            "session_version": 0, "created_at": now, "updated_at": now,
        })
        user_id = str(result.inserted_id)
        generate_and_store_user_keys(db, secret_key, user_id)
        return user_id

    make("Admin User", "admin@kyberchat.test", "admin", "AdminPass123!", "admin")
    make("Alice", "alice@kyberchat.test", "alice", "AlicePass123!", "user")
    make("Bob", "bob@kyberchat.test", "bob", "BobPass123!", "user")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5055
    client = mongomock.MongoClient()
    db = client["kyberchat_integration"]
    seed(db, os.environ["SECRET_KEY"])

    app = create_app(db_override=db)
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
