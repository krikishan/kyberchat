"""
Classical RSA workflow, provided ONLY for benchmarking comparison against
ML-KEM (see docs/crypto-design.md, section "ML-KEM vs RSA"). RSA is NOT part
of the application's actual message encryption path — that always uses
ML-KEM -> HKDF -> AES-256-GCM.

RSA and ML-KEM are not the same kind of primitive:
  - ML-KEM is a post-quantum Key Encapsulation Mechanism.
  - RSA here is used for a classical key-transport operation (RSA-OAEP
    wrapping of a random symmetric key), which is the fair classical
    analogue of "establish a shared secret", for timing/size comparison.

Uses the maintained `cryptography` library — no hand-rolled RSA math.
"""
from __future__ import annotations

import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

ALGORITHM = "RSA-3072-OAEP"
RSA_KEY_SIZE = 3072  # roughly comparable classical security margin
RSA_PUBLIC_EXPONENT = 65537


def generate_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=RSA_PUBLIC_EXPONENT, key_size=RSA_KEY_SIZE
    )
    public_key = private_key.public_key()
    return private_key, public_key


def wrap_key(public_key, symmetric_key: bytes | None = None) -> tuple[bytes, bytes]:
    """
    Classical analogue of ML-KEM encapsulation: generate a random symmetric
    key and encrypt ("wrap") it under the recipient's RSA public key.
    Returns (rsa_ciphertext, symmetric_key).
    """
    if symmetric_key is None:
        symmetric_key = os.urandom(32)
    ciphertext = public_key.encrypt(
        symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return ciphertext, symmetric_key


def unwrap_key(private_key, ciphertext: bytes) -> bytes:
    """Classical analogue of ML-KEM decapsulation."""
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def serialize_public_key(public_key) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
