"""
MongoDB Atlas connection. A single MongoClient is created once per process
and reused (pymongo pools connections internally) — we never open a new
connection per request.
"""
from pymongo import ASCENDING, MongoClient
from pymongo.database import Database

_client: MongoClient | None = None
_db: Database | None = None


def init_db(app) -> Database:
    global _client, _db
    if _db is not None:
        return _db

    uri = app.config["MONGODB_URI"]
    use_tls = uri.startswith("mongodb+srv://") or "mongodb.net" in uri
    _client = MongoClient(uri, tls=use_tls, serverSelectionTimeoutMS=8000)
    _db = _client[app.config["MONGODB_DB_NAME"]]
    _create_indexes(_db)
    app.db = _db
    return _db


def get_db() -> Database:
    if _db is None:
        raise RuntimeError("Database not initialized — call init_db(app) first")
    return _db


def ping() -> bool:
    try:
        _client.admin.command("ping")
        return True
    except Exception:
        return False


def _create_indexes(db: Database) -> None:
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("username", ASCENDING)], unique=True)
    db.conversations.create_index([("participants", ASCENDING)])
    db.messages.create_index([("conversation_id", ASCENDING), ("timestamp", ASCENDING)])
    db.groups.create_index([("members", ASCENDING)])
    db.group_members.create_index([("group_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
    db.files.create_index([("file_id", ASCENDING)], unique=True)
    db.files.create_index([("conversation_id", ASCENDING)])
    db.files.create_index([("group_id", ASCENDING)])
    db.key_metadata.create_index([("user_id", ASCENDING)])
    db.key_metadata.create_index([("key_id", ASCENDING)], unique=True)
    db.performance_results.create_index([("algorithm", ASCENDING), ("operation", ASCENDING)])
    db.audit_logs.create_index([("timestamp", ASCENDING)])
    db.private_keys.create_index([("key_id", ASCENDING)], unique=True)
    db.private_keys.create_index([("user_id", ASCENDING)])
    db.session_metadata.create_index([("context_type", ASCENDING), ("context_id", ASCENDING), ("key_version", ASCENDING)], unique=True)
    db.session_keys.create_index([("context_type", ASCENDING), ("context_id", ASCENDING), ("key_version", ASCENDING), ("user_id", ASCENDING)], unique=True)
    db.user_preferences.create_index([("owner_id", ASCENDING)], unique=True)
