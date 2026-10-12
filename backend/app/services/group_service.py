import datetime
import uuid

from app.crypto import session_manager


class GroupError(Exception):
    def __init__(self, message: str, code: str = "error"):
        super().__init__(message)
        self.code = code


def create_group(db, app_secret_key: str, creator_id: str, group_name: str, member_ids: list[str]) -> dict:
    group_name = (group_name or "").strip()
    if not group_name:
        raise GroupError("Group name is required.", "invalid_name")

    all_members = sorted(set(member_ids) | {creator_id})
    group_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow()

    session_manager.establish_session(db, app_secret_key, "group", group_id, all_members)

    doc = {
        "group_id": group_id,
        "group_name": group_name,
        "creator_id": creator_id,
        "members": all_members,
        "created_at": now,
        "updated_at": now,
    }
    db.groups.insert_one(doc)
    for member_id in all_members:
        db.group_members.insert_one({"group_id": group_id, "user_id": member_id, "joined_at": now})
    return doc


def require_member(group: dict, user_id: str) -> None:
    if user_id not in group.get("members", []):
        raise GroupError("You are not authorized to access this group.", "unauthorized")


def _rotate(db, app_secret_key: str, group: dict) -> None:
    session_manager.establish_session(db, app_secret_key, "group", group["group_id"], group["members"])


def add_member(db, app_secret_key: str, group_id: str, requester_id: str, new_member_id: str) -> dict:
    group = db.groups.find_one({"group_id": group_id})
    if not group:
        raise GroupError("Group not found.", "not_found")
    if requester_id != group["creator_id"]:
        raise GroupError("Only the group creator can manage membership.", "unauthorized")
    if new_member_id in group["members"]:
        raise GroupError("User is already a member.", "already_member")

    now = datetime.datetime.utcnow()
    updated_members = sorted(group["members"] + [new_member_id])
    db.groups.update_one({"group_id": group_id}, {"$set": {"members": updated_members, "updated_at": now}})
    db.group_members.insert_one({"group_id": group_id, "user_id": new_member_id, "joined_at": now})

    group["members"] = updated_members
    _rotate(db, app_secret_key, group)  # new member gets the NEW version only — no history access
    return group


def remove_member(db, app_secret_key: str, group_id: str, requester_id: str, target_member_id: str) -> dict:
    group = db.groups.find_one({"group_id": group_id})
    if not group:
        raise GroupError("Group not found.", "not_found")
    if requester_id != group["creator_id"]:
        raise GroupError("Only the group creator can manage membership.", "unauthorized")
    if target_member_id not in group["members"]:
        raise GroupError("User is not a member.", "not_member")

    now = datetime.datetime.utcnow()
    updated_members = [m for m in group["members"] if m != target_member_id]
    db.groups.update_one({"group_id": group_id}, {"$set": {"members": updated_members, "updated_at": now}})
    db.group_members.delete_one({"group_id": group_id, "user_id": target_member_id})

    group["members"] = updated_members
    if updated_members:
        _rotate(db, app_secret_key, group)  # removed member gets no wrapped copy of the new key
    return group


def send_message(db, app_secret_key: str, group_id: str, sender_id: str, plaintext: str, message_type: str = "text") -> dict:
    group = db.groups.find_one({"group_id": group_id})
    if not group:
        raise GroupError("Group not found.", "not_found")
    require_member(group, sender_id)

    encrypted = session_manager.encrypt_for_context(
        db, app_secret_key, "group", group_id, sender_id, plaintext.encode("utf-8")
    )
    message_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow()
    doc = {
        "message_id": message_id,
        "group_id": group_id,
        "sender_id": sender_id,
        "message_type": message_type,
        "ciphertext": encrypted["ciphertext"],
        "nonce": encrypted["nonce"],
        "key_version": encrypted["key_version"],
        "algorithm": encrypted["algorithm"],
        "timestamp": now,
    }
    db.messages.insert_one(doc)
    db.groups.update_one({"group_id": group_id}, {"$set": {"updated_at": now}})
    return doc


def list_messages(db, app_secret_key: str, group_id: str, requesting_user_id: str) -> list[dict]:
    group = db.groups.find_one({"group_id": group_id})
    if not group:
        raise GroupError("Group not found.", "not_found")
    require_member(group, requesting_user_id)

    results = []
    for msg in db.messages.find({"group_id": group_id}).sort("timestamp", 1):
        try:
            plaintext = session_manager.decrypt_for_context(
                db, app_secret_key, "group", group_id, requesting_user_id,
                msg["ciphertext"], msg["nonce"], msg["key_version"],
            )
            content = plaintext.decode("utf-8")
        except PermissionError:
            # Member joined after this message's key version was retired for
            # them — they were never issued a wrapped copy of that version.
            content = None
        results.append({
            "message_id": msg["message_id"],
            "sender_id": msg["sender_id"],
            "content": content,
            "accessible": content is not None,
            "timestamp": msg["timestamp"].isoformat(),
            "message_type": msg.get("message_type", "text"),
        })
    return results
