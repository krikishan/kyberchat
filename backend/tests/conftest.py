import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-not-for-production")
os.environ.setdefault("MONGODB_URI", "mongodb://unused-because-of-db-override")
os.environ.setdefault("FLASK_ENV", "development")

import mongomock
import pytest

from app import create_app
from app.auth.passwords import hash_password
from app.auth.tokens import issue_token


@pytest.fixture
def db():
    client = mongomock.MongoClient()
    return client["kyberchat_test"]


@pytest.fixture
def app(db, monkeypatch):
    # Never make real SMTP calls in tests.
    monkeypatch.setattr("app.services.user_service.send_credentials_email", lambda *a, **k: None)
    application = create_app(db_override=db)
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def _make_user(db, name, email, username, role, password="Password123!", secret_key="test-secret-key-not-for-production"):
    now = datetime.datetime.utcnow()
    result = db.users.insert_one({
        "name": name, "email": email, "username": username,
        "password_hash": hash_password(password), "role": role,
        "status": "active", "must_change_password": False,
        "session_version": 0, "created_at": now, "updated_at": now,
    })
    user_id = str(result.inserted_id)
    from app.crypto.key_directory import generate_and_store_user_keys
    generate_and_store_user_keys(db, secret_key, user_id)
    return user_id


@pytest.fixture
def admin_token(app, db):
    with app.app_context():
        user_id = _make_user(db, "Admin", "admin@kyberchat.test", "admin", "admin")
        return issue_token(user_id, "admin", 0), user_id


@pytest.fixture
def user_token(app, db):
    with app.app_context():
        user_id = _make_user(db, "Regular User", "user@kyberchat.test", "reguser", "user")
        return issue_token(user_id, "user", 0), user_id


@pytest.fixture
def second_user_token(app, db):
    with app.app_context():
        user_id = _make_user(db, "Second User", "second@kyberchat.test", "seconduser", "user")
        return issue_token(user_id, "user", 0), user_id


@pytest.fixture
def third_user_token(app, db):
    with app.app_context():
        user_id = _make_user(db, "Third User", "third@kyberchat.test", "thirduser", "user")
        return issue_token(user_id, "user", 0), user_id
