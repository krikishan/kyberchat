import datetime

from email_validator import EmailNotValidError, validate_email as _validate_email

from app.auth.passwords import generate_temporary_password, generate_username, hash_password
from app.crypto.key_directory import generate_and_store_user_keys
from app.email.mailer import EmailDeliveryError, send_credentials_email
from app.services.audit_log import record_event


class UserCreationError(Exception):
    def __init__(self, message: str, code: str = "creation_failed"):
        super().__init__(message)
        self.code = code


def normalize_email(raw_email: str) -> str:
    return raw_email.strip().lower()


def validate_email_format(email: str) -> str:
    try:
        result = _validate_email(email, check_deliverability=False)
        return result.normalized
    except EmailNotValidError as exc:
        raise UserCreationError(f"Invalid email address: {email}", code="invalid_email") from exc


def email_exists(db, email: str) -> bool:
    return db.users.find_one({"email": email}) is not None


def username_exists(db, username: str) -> bool:
    return db.users.find_one({"username": username}) is not None


def create_single_user(db, app_config, name: str, email: str, role: str = "user", team_id: str | None = None) -> dict:
    """
    Full flow (spec section 7):
    validate -> check duplicate -> generate username/password -> send email FIRST
    -> only then insert the account (never create silently if email required and fails).
    Raises UserCreationError on any failure; caller (route) turns this into an HTTP response.
    """
    # Only 'user' and 'admin' can be created through the API — developer is bootstrap-only.
    if role not in ("user", "admin"):
        raise UserCreationError("Invalid role.", code="invalid_role")
    name = (name or "").strip()
    if not name:
        raise UserCreationError("Name is required.", code="invalid_name")

    email = validate_email_format(normalize_email(email))

    if email_exists(db, email):
        raise UserCreationError(f"An account with email {email} already exists.", code="duplicate_email")

    username = generate_username(name, lambda u: username_exists(db, u))
    temp_password = generate_temporary_password()
    password_hash = hash_password(temp_password)

    try:
        send_credentials_email(app_config, to_email=email, name=name, username=username, temporary_password=temp_password)
    except EmailDeliveryError as exc:
        raise UserCreationError(str(exc), code="email_delivery_failed") from exc

    team_name = None
    if team_id:
        team = db.teams.find_one({"team_id": team_id})
        if team:
            team_name = team.get("name")

    now = datetime.datetime.utcnow()
    result = db.users.insert_one({
        "name": name,
        "email": email,
        "username": username,
        "password_hash": password_hash,
        "role": role,
        "status": "active",
        "team_id": team_id,
        "team_name": team_name,
        "must_change_password": True,
        "session_version": 0,
        "created_at": now,
        "updated_at": now,
    })
    user_id = str(result.inserted_id)

    if role == "admin" and team_id:
        db.teams.update_one({"team_id": team_id}, {"$set": {"lead_id": user_id}})

    generate_and_store_user_keys(db, app_config["SECRET_KEY"], user_id)
    record_event(db, event_type="user_created", details={"user_id": user_id, "role": role, "team_id": team_id})

    return {"id": user_id, "name": name, "email": email, "username": username, "role": role, "team_id": team_id, "team_name": team_name}
