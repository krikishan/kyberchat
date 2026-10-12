"""Reset admin password to a known value."""
from dotenv import load_dotenv
load_dotenv('../.env')
from app import create_app
from app.auth.passwords import hash_password

NEW_PASSWORD = "KyberAdmin@2025!"

app = create_app()
with app.app_context():
    db = app.db
    result = db.users.update_one(
        {"username": "admin"},
        {"$set": {
            "password_hash": hash_password(NEW_PASSWORD),
            "must_change_password": False,
            "session_version": 0,
        }}
    )
    if result.modified_count:
        print(f"Password reset successfully.")
        print(f"Username: admin")
        print(f"Password: {NEW_PASSWORD}")
    else:
        print("No user found with username 'admin'")
        # List all users
        users = list(db.users.find({}, {"username": 1, "role": 1, "_id": 0}))
        print("Existing users:", users)
