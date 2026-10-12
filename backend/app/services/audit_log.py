import datetime


def record_event(db, event_type: str, user_id: str | None = None, details: dict | None = None):
    """details must never contain passwords, keys, tokens, or plaintext message content."""
    db.audit_logs.insert_one({
        "event_type": event_type,
        "user_id": user_id,
        "details": details or {},
        "timestamp": datetime.datetime.utcnow(),
    })
