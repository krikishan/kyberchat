"""Bootstrap script: creates the initial Developer account.

Run once:  python bootstrap_admin.py
If an account with username 'admin' already exists, it is upgraded to 'developer' role.
"""
from app import create_app
from app.auth.passwords import hash_password
from app.crypto.key_directory import generate_and_store_user_keys
import datetime

app = create_app()
with app.app_context():
    db = app.db
    now = datetime.datetime.utcnow()

    existing = db.users.find_one({"username": "admin"})
    if existing:
        if existing.get("role") == "developer":
            print("Developer already exists:", existing["_id"])
        else:
            # Upgrade existing admin to developer role
            db.users.update_one(
                {"_id": existing["_id"]},
                {"$set": {"role": "developer", "updated_at": now}},
            )
            print("Upgraded existing admin to developer:", existing["_id"])
    else:
        result = db.users.insert_one({
            "name": "Developer", "email": "admin@example.com", "username": "admin",
            "password_hash": hash_password("ChangeThisTemporaryPassword1!"),
            "role": "developer", "status": "active", "must_change_password": True,
            "session_version": 0, "created_at": now, "updated_at": now,
        })
        generate_and_store_user_keys(db, app.config["SECRET_KEY"], str(result.inserted_id))
        print("Developer created:", result.inserted_id)
