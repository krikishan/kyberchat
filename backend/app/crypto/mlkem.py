"""
ML-KEM (FIPS 203) key encapsulation, via the maintained `pqcrypto` library
(Rust bindings to PQClean's ML-KEM-768 implementation).

We do NOT implement ML-KEM's math ourselves. This module only wraps
keygen/encaps/decaps and attaches non-secret metadata (key id, fingerprint,
version, timestamps) for the trust-model / key-directory described in
docs/crypto-design.md.

IMPORTANT: ML-KEM is a Key Encapsulation Mechanism, not a message cipher.
It produces a shared secret; that secret is fed into HKDF (see hkdf.py) to
derive an application key, which AES-256-GCM (see aes_gcm.py) then uses to
actually encrypt data. Never use the raw ML-KEM shared secret directly as
an AES key.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass

from pqcrypto.kem.ml_kem_768 import (
    keygen as _keygen,
    encaps as _encaps,
    decaps as _decaps,
    PUBLIC_KEY_SIZE,
    SECRET_KEY_SIZE,
    CIPHERTEXT_SIZE,
    SHARED_SECRET_SIZE,
)

ALGORITHM = "ML-KEM-768"


@dataclass
class MLKEMKeyPair:
    key_id: str
    public_key: bytes
    secret_key: bytes
    fingerprint: str
    algorithm: str
    version: int
    created_at: float

    def public_metadata(self) -> dict:
        """Safe to store/return via API — never includes secret_key."""
        return {
            "key_id": self.key_id,
            "algorithm": self.algorithm,
            "version": self.version,
            "fingerprint": self.fingerprint,
            "public_key": self.public_key.hex(),
            "created_at": self.created_at,
        }


def _fingerprint(public_key: bytes) -> str:
    # SHA-256 of the public key, truncated for display — not secret material.
    return hashlib.sha256(public_key).hexdigest()[:16]


def generate_keypair(version: int = 1) -> MLKEMKeyPair:
    """User B: generate an ML-KEM-768 key pair. Call once per user/key-version."""
    public_key, secret_key = _keygen()
    assert len(public_key) == PUBLIC_KEY_SIZE
    assert len(secret_key) == SECRET_KEY_SIZE
    return MLKEMKeyPair(
        key_id=str(uuid.uuid4()),
        public_key=public_key,
        secret_key=secret_key,
        fingerprint=_fingerprint(public_key),
        algorithm=ALGORITHM,
        version=version,
        created_at=time.time(),
    )


def encapsulate(recipient_public_key: bytes) -> tuple[bytes, bytes]:
    """
    User A: given User B's authenticated public key, perform encapsulation.
    Returns (kem_ciphertext, shared_secret). kem_ciphertext must be sent to
    User B; shared_secret is fed into HKDF locally and never transmitted.
    """
    if len(recipient_public_key) != PUBLIC_KEY_SIZE:
        raise ValueError("Invalid ML-KEM public key length")
    ciphertext, shared_secret = _encaps(recipient_public_key)
    assert len(ciphertext) == CIPHERTEXT_SIZE
    assert len(shared_secret) == SHARED_SECRET_SIZE
    return ciphertext, shared_secret


def decapsulate(secret_key: bytes, kem_ciphertext: bytes) -> bytes:
    """User B: recover the shared secret from the received KEM ciphertext."""
    if len(kem_ciphertext) != CIPHERTEXT_SIZE:
        raise ValueError("Invalid ML-KEM ciphertext length")
    shared_secret = _decaps(secret_key, kem_ciphertext)
    assert len(shared_secret) == SHARED_SECRET_SIZE
    return shared_secret
