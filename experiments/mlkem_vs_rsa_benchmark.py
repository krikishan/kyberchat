"""
Real cryptographic benchmark: ML-KEM-768 vs RSA-3072, plus HKDF and
AES-256-GCM. Runs actual operations for N trials and computes
avg/min/max/stdev. Writes results to experiments/results/benchmark_results.json.

Usage:
    python experiments/mlkem_vs_rsa_benchmark.py --trials 30
"""
import argparse
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "app"))

from crypto import mlkem, hkdf, aes_gcm, rsa_compare  # noqa: E402


def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, elapsed_ms


def stats(values):
    return {
        "avg_ms": round(statistics.mean(values), 4),
        "min_ms": round(min(values), 4),
        "max_ms": round(max(values), 4),
        "stdev_ms": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
        "trials": len(values),
    }


def run(trials: int):
    results = {}

    # --- ML-KEM-768 ---
    keygen_times, encaps_times, decaps_times = [], [], []
    ciphertext_size = None
    for _ in range(trials):
        keypair, t_keygen = timed(mlkem.generate_keypair)
        keygen_times.append(t_keygen)
        (ct, ss_a), t_encaps = timed(mlkem.encapsulate, keypair.public_key)
        encaps_times.append(t_encaps)
        ciphertext_size = len(ct)
        _, t_decaps = timed(mlkem.decapsulate, keypair.secret_key, ct)
        decaps_times.append(t_decaps)

    results["ML-KEM-768"] = {
        "key_generation": stats(keygen_times),
        "encapsulation": stats(encaps_times),
        "decapsulation": stats(decaps_times),
        "ciphertext_size_bytes": ciphertext_size,
        "public_key_size_bytes": mlkem.PUBLIC_KEY_SIZE if hasattr(mlkem, "PUBLIC_KEY_SIZE") else None,
    }

    # --- RSA-3072 (classical comparison) ---
    keygen_times, wrap_times, unwrap_times = [], [], []
    rsa_ciphertext_size = None
    for _ in range(trials):
        (priv, pub), t_keygen = timed(rsa_compare.generate_keypair)
        keygen_times.append(t_keygen)
        (ct, sym_key), t_wrap = timed(rsa_compare.wrap_key, pub)
        wrap_times.append(t_wrap)
        rsa_ciphertext_size = len(ct)
        _, t_unwrap = timed(rsa_compare.unwrap_key, priv, ct)
        unwrap_times.append(t_unwrap)

    results["RSA-3072-OAEP"] = {
        "key_generation": stats(keygen_times),
        "key_wrap_operation": stats(wrap_times),
        "key_unwrap_operation": stats(unwrap_times),
        "wrapped_key_ciphertext_size_bytes": rsa_ciphertext_size,
    }

    # --- HKDF ---
    hkdf_times = []
    for _ in range(trials):
        secret = os.urandom(32)
        salt = hkdf.generate_salt()
        _, t = timed(hkdf.derive_session_key, secret, salt, "benchmark-context")
        hkdf_times.append(t)
    results["HKDF-SHA256"] = {"derivation": stats(hkdf_times)}

    # --- AES-256-GCM, varying payload size ---
    aes_results = {}
    for size_label, size_bytes in [("1KB", 1024), ("10KB", 10 * 1024), ("100KB", 100 * 1024)]:
        payload = os.urandom(size_bytes)
        key = os.urandom(32)
        enc_times, dec_times = [], []
        for _ in range(trials):
            enc_result, t_enc = timed(aes_gcm.encrypt, key, payload)
            enc_times.append(t_enc)
            _, t_dec = timed(aes_gcm.decrypt, key, enc_result.nonce, enc_result.ciphertext)
            dec_times.append(t_dec)
        aes_results[size_label] = {"encryption": stats(enc_times), "decryption": stats(dec_times)}
    results["AES-256-GCM"] = aes_results

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=30)
    args = parser.parse_args()

    output = run(args.trials)
    os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "results", "benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(output, indent=2))
    print(f"\nSaved to {out_path}")
