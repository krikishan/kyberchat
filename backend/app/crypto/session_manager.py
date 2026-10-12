"""
Session-key establishment for both individual conversations and groups,
using one unified mechanism (spec sections 11, 12, 14):

  1. Generate a fresh random session key (the actual AES-256-GCM message key)
     for this context (conversation_id or group_id) and version.
  2. For EACH current member, perform an independent ML-KEM encapsulation
     against that member's own public key, derive a per-member *wrapping*
     key via HKDF, and AES-256-GCM-encrypt ("wrap") the shared session key
     under it. This is standard hybrid/broadcast key-wrapping — NOT one
     hard-coded key for every group, and each member's wrapped copy is only
     openable with that member's own ML-KEM private key.
  3. To read messages, a member decapsulates their own wrapped entry (using
     their private key), re-derives the wrapping key via HKDF, and unwraps
     the shared session key. That recovered session key is identical for
     every member of that version — it's the same AES key, just delivered
     differently to each person.

Membership-change key rotation:
  - On join, leave, or removal: a NEW session key is generated (version+1)
    and wrapped only for the *current* member list. A member removed from
    the group is not given a wrapped copy of the new version, so they
    cannot decrypt any message sent after removal (no forward access).
  - A member who joins later is likewise not given a wrapped copy of any
    *older* version, so they cannot decrypt history from before they
    joined. This is a deliberate, documented simplification appropriate
    for a college project — not a full MLS-style ratchet.
"""
from __future__ import annotations

import os
import time

from app.crypto import mlkem, hkdf as hkdf_mod, aes_gcm
from app.crypto.key_directory import get_active_public_key, get_decrypted_private_key_for_user

SESSION_KEY_LEN = 32


def _wrap_context(context_type: str, context_id: str, version: int) -> str:
    return f"{context_type}:{context_id}:v{version}:wrap"


def _latest_version(db, context_type: str, context_id: str) -> int:
    doc = db.session_metadata.find_one(
        {"context_type": context_type, "context_id": context_id},
        sort=[("key_version", -1)],
    )
    return doc["key_version"] if doc else 0


def establish_session(db, app_secret_key: str, context_type: str, context_id: str, member_user_ids: list[str]) -> int:
    """Creates a new session-key version and wraps it for exactly the given
    members. Marks any prior version 'retired'. Returns the new version number."""
    if not member_user_ids:
        raise ValueError("A session needs at least one member")

    new_version = _latest_version(db, context_type, context_id) + 1
    session_key = os.urandom(SESSION_KEY_LEN)

    db.session_metadata.update_many(
        {"context_type": context_type, "context_id": context_id, "status": "active"},
        {"$set": {"status": "retired"}},
    )
    db.session_metadata.insert_one({
        "context_type": context_type,
        "context_id": context_id,
        "key_version": new_version,
        "algorithm": "ML-KEM-768+HKDF-SHA256+AES-256-GCM",
        "member_count": len(member_user_ids),
        "created_at": time.time(),
        "status": "active",
    })

    wrap_ctx = _wrap_context(context_type, context_id, new_version)
    for user_id in member_user_ids:
        pub_meta = get_active_public_key(db, user_id)
        if not pub_meta:
            raise ValueError(f"User {user_id} has no ML-KEM public key on file")
        public_key = bytes.fromhex(pub_meta["public_key"])

        kem_ciphertext, shared_secret = mlkem.encapsulate(public_key)
        salt = hkdf_mod.generate_salt()
        wrapping_key = hkdf_mod.derive_session_key(shared_secret, salt, context_id=wrap_ctx)
        wrapped = aes_gcm.encrypt(wrapping_key, session_key)

        db.session_keys.insert_one({
            "context_type": context_type,
            "context_id": context_id,
            "key_version": new_version,
            "user_id": user_id,
            "recipient_key_id": pub_meta["key_id"],
            "kem_ciphertext": kem_ciphertext.hex(),
            "salt": salt.hex(),
            "wrapped_ciphertext": wrapped.ciphertext.hex(),
            "wrapped_nonce": wrapped.nonce.hex(),
        })

    return new_version


def get_session_key(db, app_secret_key: str, context_type: str, context_id: str, user_id: str, key_version: int | None = None) -> tuple[bytes, int]:
    """A member recovers the shared session key for a given (or latest active) version."""
    if key_version is None:
        meta = db.session_metadata.find_one(
            {"context_type": context_type, "context_id": context_id, "status": "active"}
        )
        if not meta:
            raise ValueError("No active session for this context")
        key_version = meta["key_version"]

    wrapped_entry = db.session_keys.find_one({
        "context_type": context_type, "context_id": context_id,
        "key_version": key_version, "user_id": user_id,
    })
    if not wrapped_entry:
        raise PermissionError("This user has no wrapped session key for this version — not authorized for this period.")

    private_key, _key_id = get_decrypted_private_key_for_user(db, app_secret_key, user_id)
    shared_secret = mlkem.decapsulate(private_key, bytes.fromhex(wrapped_entry["kem_ciphertext"]))
    wrap_ctx = _wrap_context(context_type, context_id, key_version)
    wrapping_key = hkdf_mod.derive_session_key(shared_secret, bytes.fromhex(wrapped_entry["salt"]), context_id=wrap_ctx)
    session_key = aes_gcm.decrypt(wrapping_key, bytes.fromhex(wrapped_entry["wrapped_nonce"]), bytes.fromhex(wrapped_entry["wrapped_ciphertext"]))
    return session_key, key_version


def encrypt_for_context(db, app_secret_key: str, context_type: str, context_id: str, sender_user_id: str, plaintext: bytes) -> dict:
    session_key, version = get_session_key(db, app_secret_key, context_type, context_id, sender_user_id)
    result = aes_gcm.encrypt(session_key, plaintext, associated_data=context_id.encode())
    return {
        "ciphertext": result.ciphertext.hex(),
        "nonce": result.nonce.hex(),
        "key_version": version,
        "algorithm": "AES-256-GCM",
    }


def decrypt_for_context(db, app_secret_key: str, context_type: str, context_id: str, reader_user_id: str, ciphertext_hex: str, nonce_hex: str, key_version: int) -> bytes:
    session_key, _ = get_session_key(db, app_secret_key, context_type, context_id, reader_user_id, key_version)
    return aes_gcm.decrypt(session_key, bytes.fromhex(nonce_hex), bytes.fromhex(ciphertext_hex), associated_data=context_id.encode())
