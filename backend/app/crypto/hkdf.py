"""
HKDF (RFC 5869) derivation of an application/session key from an ML-KEM
shared secret. Uses `cryptography`'s HKDF implementation — not hand-rolled.

Design (documented in docs/crypto-design.md):
  - Hash algorithm: SHA-256
  - Salt: a fresh random 32-byte salt generated per key-establishment event
    and transmitted alongside the ML-KEM ciphertext (salt is not secret).
  - Info/context: a fixed, versioned context string that binds the derived
    key to this application and purpose, plus the conversation/group id so
    keys are never reused across contexts.

Both parties independently compute the same derived key because they both
have: (shared_secret, salt, info). Only the shared_secret is secret.
"""
from __future__ import annotations

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

HKDF_HASH = hashes.SHA256()
DERIVED_KEY_LEN = 32  # 256-bit key for AES-256-GCM
APP_CONTEXT = b"kyberchat-v1"


def generate_salt() -> bytes:
    return os.urandom(32)


def derive_session_key(shared_secret: bytes, salt: bytes, context_id: str) -> bytes:
    """
    context_id: conversation_id or group_id + key_version, so a key derived
    for one conversation can never be replayed as the key for another.
    """
    info = APP_CONTEXT + b"|" + context_id.encode("utf-8")
    hkdf = HKDF(
        algorithm=HKDF_HASH,
        length=DERIVED_KEY_LEN,
        salt=salt,
        info=info,
    )
    return hkdf.derive(shared_secret)
