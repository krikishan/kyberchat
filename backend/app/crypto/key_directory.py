"""
Manages the authenticated public-key directory (spec section 16/17).

Private keys must be protected at rest. Since this is a server-held-key
architecture (no persistent client-side key storage in a stateless web app),
we encrypt each user's ML-KEM private key with AES-256-GCM under a key
derived (via HKDF) from the server's SECRET_KEY, and store the encrypted
blob separately from the public, non-secret key_metadata document.

This is documented as an academic-prototype trust assumption in
docs/crypto-design.md: it protects against raw DB dumps/backups exposing
private keys, but a full backend compromise (with SECRET_KEY) can still
decrypt them. That's stated plainly, not hidden.
"""
from __future__ import annotations

from app.crypto import mlkem, hkdf as hkdf_mod, aes_gcm


def _master_key(secret_key: str) -> bytes:
    # Derive a stable 32-byte encryption key for wrapping private keys.
    salt = b"kyberchat-key-directory-salt-v1"  # fixed, non-secret context salt
    return hkdf_mod.derive_session_key(secret_key.encode("utf-8"), salt, context_id="private-key-encryption")


def generate_and_store_user_keys(db, app_secret_key: str, user_id: str) -> dict:
    """Generates an ML-KEM keypair for a new user, encrypts the private key,
    and stores both the public metadata (key_metadata) and the encrypted
    private key (private_keys) in Mongo. Returns the safe public metadata."""
    keypair = mlkem.generate_keypair()
    master_key = _master_key(app_secret_key)
    encrypted = aes_gcm.encrypt(master_key, keypair.secret_key)

    db.key_metadata.insert_one({
        "key_id": keypair.key_id,
        "user_id": user_id,
        "algorithm": keypair.algorithm,
        "key_version": keypair.version,
        "fingerprint": keypair.fingerprint,
        "public_key": keypair.public_key.hex(),
        "created_at": keypair.created_at,
        "status": "active",
    })
    db.private_keys.insert_one({
        "key_id": keypair.key_id,
        "user_id": user_id,
        "ciphertext": encrypted.ciphertext.hex(),
        "nonce": encrypted.nonce.hex(),
    })
    return keypair.public_metadata()


def get_decrypted_private_key(db, app_secret_key: str, key_id: str) -> bytes:
    """Server-side use only (message decryption path). Never returned via API."""
    record = db.private_keys.find_one({"key_id": key_id})
    if not record:
        raise ValueError("Key not found")
    master_key = _master_key(app_secret_key)
    return aes_gcm.decrypt(master_key, bytes.fromhex(record["nonce"]), bytes.fromhex(record["ciphertext"]))


def get_active_public_key(db, user_id: str) -> dict | None:
    return db.key_metadata.find_one({"user_id": user_id, "status": "active"}, {"_id": 0})


def get_decrypted_private_key_for_user(db, app_secret_key: str, user_id: str) -> tuple[bytes, str]:
    """Server-side use only. Returns (private_key_bytes, key_id)."""
    meta = get_active_public_key(db, user_id)
    if not meta:
        raise ValueError(f"No active ML-KEM key for user {user_id}")
    return get_decrypted_private_key(db, app_secret_key, meta["key_id"]), meta["key_id"]
