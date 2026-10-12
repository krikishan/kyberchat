"""
Encryption/decryption simulation (spec section 22) — runs the REAL crypto
pipeline end-to-end on a sample message and reports each stage's timing and
safe, non-secret metadata. Never returns private keys, raw session keys,
passwords, or API keys.
"""
import time

from app.crypto import mlkem, hkdf as hkdf_mod, aes_gcm


def run_simulation(sample_message: str) -> dict:
    stages = []
    plaintext = sample_message.encode("utf-8")

    t0 = time.perf_counter()
    keypair_b = mlkem.generate_keypair()
    t1 = time.perf_counter()
    stages.append({
        "stage": "ML-KEM Key Generation (Receiver)",
        "algorithm": mlkem.ALGORITHM,
        "key_id": keypair_b.key_id,
        "fingerprint": keypair_b.fingerprint,
        "duration_ms": round((t1 - t0) * 1000, 4),
    })

    t0 = time.perf_counter()
    kem_ciphertext, shared_secret_a = mlkem.encapsulate(keypair_b.public_key)
    t1 = time.perf_counter()
    stages.append({
        "stage": "ML-KEM Encapsulation (Sender)",
        "algorithm": mlkem.ALGORITHM,
        "kem_ciphertext_size_bytes": len(kem_ciphertext),
        "duration_ms": round((t1 - t0) * 1000, 4),
    })

    t0 = time.perf_counter()
    salt = hkdf_mod.generate_salt()
    session_key = hkdf_mod.derive_session_key(shared_secret_a, salt, context_id="simulation")
    t1 = time.perf_counter()
    stages.append({
        "stage": "HKDF Session Key Derivation",
        "algorithm": "HKDF-SHA256",
        "derived_key_length_bytes": len(session_key),
        "duration_ms": round((t1 - t0) * 1000, 4),
    })

    t0 = time.perf_counter()
    result = aes_gcm.encrypt(session_key, plaintext)
    t1 = time.perf_counter()
    stages.append({
        "stage": "AES-256-GCM Encryption",
        "algorithm": "AES-256-GCM",
        "ciphertext_preview": result.ciphertext.hex()[:32] + "...",
        "ciphertext_size_bytes": len(result.ciphertext),
        "nonce_hex": result.nonce.hex(),
        "duration_ms": round((t1 - t0) * 1000, 4),
    })

    stages.append({"stage": "Transmission", "note": "Ciphertext + nonce + KEM ciphertext transmitted to receiver."})

    t0 = time.perf_counter()
    shared_secret_b = mlkem.decapsulate(keypair_b.secret_key, kem_ciphertext)
    session_key_b = hkdf_mod.derive_session_key(shared_secret_b, salt, context_id="simulation")
    t1 = time.perf_counter()
    stages.append({
        "stage": "ML-KEM Decapsulation + HKDF (Receiver)",
        "duration_ms": round((t1 - t0) * 1000, 4),
        "keys_match": session_key_b == session_key,  # safe boolean, never the key itself
    })

    t0 = time.perf_counter()
    try:
        recovered = aes_gcm.decrypt(session_key_b, result.nonce, result.ciphertext)
        auth_ok = True
    except aes_gcm.DecryptionError:
        recovered = b""
        auth_ok = False
    t1 = time.perf_counter()
    stages.append({
        "stage": "AES-256-GCM Decryption + Authentication",
        "authentication_verified": auth_ok,
        "duration_ms": round((t1 - t0) * 1000, 4),
    })

    return {
        "original_message": sample_message,
        "recovered_message": recovered.decode("utf-8") if auth_ok else None,
        "success": auth_ok and recovered == plaintext,
        "stages": stages,
    }
