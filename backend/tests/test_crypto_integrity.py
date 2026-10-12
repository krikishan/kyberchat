"""
Cryptographic integrity tests (spec section 56).

Run with:  pytest backend/tests/test_crypto_integrity.py -v
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest

from crypto import mlkem, hkdf, aes_gcm, rsa_compare


def test_mlkem_shared_secret_agreement():
    # User B generates a key pair
    keypair_b = mlkem.generate_keypair()

    # User A encapsulates against B's public key
    kem_ciphertext, shared_secret_a = mlkem.encapsulate(keypair_b.public_key)

    # User B decapsulates
    shared_secret_b = mlkem.decapsulate(keypair_b.secret_key, kem_ciphertext)

    assert shared_secret_a == shared_secret_b
    assert len(shared_secret_a) == 32


def test_mlkem_public_metadata_excludes_secret_key():
    keypair = mlkem.generate_keypair()
    meta = keypair.public_metadata()
    assert "secret_key" not in meta
    assert "public_key" in meta
    assert meta["algorithm"] == "ML-KEM-768"


def test_mlkem_invalid_public_key_rejected():
    with pytest.raises(ValueError):
        mlkem.encapsulate(b"too-short")


def test_hkdf_deterministic_for_same_inputs():
    shared_secret = os.urandom(32)
    salt = hkdf.generate_salt()
    key1 = hkdf.derive_session_key(shared_secret, salt, context_id="conv-123")
    key2 = hkdf.derive_session_key(shared_secret, salt, context_id="conv-123")
    assert key1 == key2
    assert len(key1) == 32


def test_hkdf_differs_by_context():
    shared_secret = os.urandom(32)
    salt = hkdf.generate_salt()
    key_a = hkdf.derive_session_key(shared_secret, salt, context_id="conv-123")
    key_b = hkdf.derive_session_key(shared_secret, salt, context_id="conv-456")
    assert key_a != key_b


def test_full_end_to_end_message_flow():
    """ML-KEM -> HKDF -> AES-256-GCM -> decrypt, both parties agree."""
    keypair_b = mlkem.generate_keypair()

    kem_ciphertext, shared_secret_a = mlkem.encapsulate(keypair_b.public_key)
    salt = hkdf.generate_salt()
    conversation_id = "conv-e2e-test"

    session_key_a = hkdf.derive_session_key(shared_secret_a, salt, conversation_id)

    plaintext = b"send me the report tomorrow"
    result = aes_gcm.encrypt(session_key_a, plaintext, associated_data=conversation_id.encode())

    # Recipient side
    shared_secret_b = mlkem.decapsulate(keypair_b.secret_key, kem_ciphertext)
    session_key_b = hkdf.derive_session_key(shared_secret_b, salt, conversation_id)
    recovered = aes_gcm.decrypt(
        session_key_b, result.nonce, result.ciphertext, associated_data=conversation_id.encode()
    )

    assert recovered == plaintext


def test_aes_gcm_tamper_detection():
    key = os.urandom(32)
    result = aes_gcm.encrypt(key, b"authentic message")

    tampered = bytearray(result.ciphertext)
    tampered[0] ^= 0xFF

    with pytest.raises(aes_gcm.DecryptionError):
        aes_gcm.decrypt(key, result.nonce, bytes(tampered))


def test_aes_gcm_nonce_uniqueness():
    key = os.urandom(32)
    nonces = {aes_gcm.encrypt(key, b"msg").nonce for _ in range(200)}
    assert len(nonces) == 200  # no collisions across 200 encryptions


def test_rsa_key_wrap_unwrap_roundtrip():
    private_key, public_key = rsa_compare.generate_keypair()
    ciphertext, symmetric_key = rsa_compare.wrap_key(public_key)
    recovered = rsa_compare.unwrap_key(private_key, ciphertext)
    assert recovered == symmetric_key
