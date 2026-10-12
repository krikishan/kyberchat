"""
AES-256-GCM authenticated encryption, via the `cryptography` library.

Every call generates a fresh, cryptographically random 96-bit nonce.
Never reuse a (key, nonce) pair. The nonce and auth tag are not secret and
are stored/transmitted alongside the ciphertext.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12  # 96 bits, standard for GCM


class DecryptionError(Exception):
    """Raised when authentication fails or ciphertext/tag was tampered with."""


@dataclass
class AESGCMResult:
    ciphertext: bytes  # includes appended 16-byte auth tag (AESGCM library behaviour)
    nonce: bytes


def encrypt(key: bytes, plaintext: bytes, associated_data: bytes | None = None) -> AESGCMResult:
    if len(key) != 32:
        raise ValueError("AES-256-GCM requires a 32-byte key")
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return AESGCMResult(ciphertext=ciphertext, nonce=nonce)


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes | None = None) -> bytes:
    if len(key) != 32:
        raise ValueError("AES-256-GCM requires a 32-byte key")
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, associated_data)
    except InvalidTag as exc:
        raise DecryptionError("Authentication failed — ciphertext or tag was modified") from exc
