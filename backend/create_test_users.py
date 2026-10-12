"""Create test accounts: one Team Admin and two regular Users."""
from dotenv import load_dotenv
load_dotenv('../.env')
from app import create_app
from app.auth.passwords import hash_password
from app.crypto.key_directory import generate_and_store_user_keys
import datetime

app = create_app()
with app.app_context():
    db = app.db
    now = datetime.datetime.utcnow()

    test_users = [
        {
            "name": "Sarah Chen",
            "email": "sarah@kyberchat.local",
            "username": "sarah",
            "password": "KyberUser@2025!",
            "role": "admin",   # Team Admin
        },
        {
            "name": "Alex Rivera",
            "email": "alex@kyberchat.local",
            "username": "alex",
            "password": "KyberUser@2025!",
            "role": "user",    # Regular Member
        },
        {
            "name": "Jordan Kim",
            "email": "jordan@kyberchat.local",
            "username": "jordan",
            "password": "KyberUser@2025!",
            "role": "user",    # Regular Member
        },
    ]

    for u in test_users:
        existing = db.users.find_one({"username": u["username"]})
        if existing:
            # Reset password in case it was changed
            db.users.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "password_hash": hash_password(u["password"]),
                    "must_change_password": False,
                    "session_version": 0,
                }}
            )
            print(f"[updated]  {u['role']:6} | username: {u['username']:8} | password: {u['password']}")
        else:
            result = db.users.insert_one({
                "name": u["name"],
                "email": u["email"],
                "username": u["username"],
                "password_hash": hash_password(u["password"]),
                "role": u["role"],
                "status": "active",
                "must_change_password": False,
                "session_version": 0,
                "created_at": now,
                "updated_at": now,
            })
            generate_and_store_user_keys(db, app.config["SECRET_KEY"], str(result.inserted_id))
            print(f"[created]  {u['role']:6} | username: {u['username']:8} | password: {u['password']}")

    print("\n--- All test accounts ---")
    print(f"{'Role':<12} {'Username':<10} {'Password'}")
    print(f"{'developer':<12} {'admin':<10} KyberAdmin@2025!")
    for u in test_users:
        print(f"{u['role']:<12} {u['username']:<10} {u['password']}")
