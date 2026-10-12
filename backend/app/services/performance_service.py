"""
Real performance benchmarking (spec sections 23, 24, 58) — every stored
record comes from an actually-executed operation timed with
time.perf_counter(). Nothing here is fabricated; if nothing has been run
yet, the dashboard must show "Not measured" rather than inventing numbers.
"""
import os
import platform
import time

from app.crypto import mlkem, hkdf as hkdf_mod, aes_gcm, rsa_compare


def run_and_store(db, trials: int = 10) -> int:
    """Runs real operations `trials` times each and inserts one document per
    trial into performance_results. Returns the number of records inserted."""
    environment = f"Python {platform.python_version()} on {platform.system()}"
    now = time.time()
    records = []

    for i in range(trials):
        keypair, t = _timed(mlkem.generate_keypair)
        records.append(_record("ML-KEM-768", "key_generation", None, t, None, environment, i, now))

        (ct, ss), t = _timed(mlkem.encapsulate, keypair.public_key)
        records.append(_record("ML-KEM-768", "encapsulation", None, t, len(ct), environment, i, now))

        _, t = _timed(mlkem.decapsulate, keypair.secret_key, ct)
        records.append(_record("ML-KEM-768", "decapsulation", None, t, None, environment, i, now))

        (priv, pub), t = _timed(rsa_compare.generate_keypair)
        records.append(_record("RSA-3072-OAEP", "key_generation", None, t, None, environment, i, now))

        (rsa_ct, sym_key), t = _timed(rsa_compare.wrap_key, pub)
        records.append(_record("RSA-3072-OAEP", "key_wrap", None, t, len(rsa_ct), environment, i, now))

        _, t = _timed(rsa_compare.unwrap_key, priv, rsa_ct)
        records.append(_record("RSA-3072-OAEP", "key_unwrap", None, t, None, environment, i, now))

        secret = os.urandom(32)
        salt = hkdf_mod.generate_salt()
        _, t = _timed(hkdf_mod.derive_session_key, secret, salt, "benchmark")
        records.append(_record("HKDF-SHA256", "derivation", None, t, None, environment, i, now))

        for label, size in [(1024, "1KB"), (10 * 1024, "10KB"), (100 * 1024, "100KB")]:
            payload = os.urandom(label)
            key = os.urandom(32)
            enc_result, t = _timed(aes_gcm.encrypt, key, payload)
            records.append(_record("AES-256-GCM", "encryption", label, t, len(enc_result.ciphertext), environment, i, now))
            _, t = _timed(aes_gcm.decrypt, key, enc_result.nonce, enc_result.ciphertext)
            records.append(_record("AES-256-GCM", "decryption", label, t, None, environment, i, now))

    db.performance_results.insert_many(records)
    return len(records)


def _timed(fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, (time.perf_counter() - start) * 1000


def _record(algorithm, operation, input_size, duration_ms, payload_size, environment, trial_number, timestamp):
    return {
        "algorithm": algorithm,
        "operation": operation,
        "input_size": input_size,
        "group_size": None,
        "trial_number": trial_number,
        "duration_ms": round(duration_ms, 5),
        "payload_size": payload_size,
        "timestamp": timestamp,
        "environment": environment,
    }


def get_summary(db) -> dict:
    """Aggregates avg/min/max/stdev per (algorithm, operation) from stored
    real measurements. Returns 'Not measured' for anything with zero records."""
    pipeline = [
        {"$group": {
            "_id": {"algorithm": "$algorithm", "operation": "$operation"},
            "avg_ms": {"$avg": "$duration_ms"},
            "min_ms": {"$min": "$duration_ms"},
            "max_ms": {"$max": "$duration_ms"},
            "count": {"$sum": 1},
            "values": {"$push": "$duration_ms"},
        }}
    ]
    summary = {}
    for row in db.performance_results.aggregate(pipeline):
        key = f"{row['_id']['algorithm']} / {row['_id']['operation']}"
        values = row["values"]
        mean = row["avg_ms"]
        variance = sum((v - mean) ** 2 for v in values) / len(values) if len(values) > 1 else 0
        summary[key] = {
            "avg_ms": round(mean, 5),
            "min_ms": round(row["min_ms"], 5),
            "max_ms": round(row["max_ms"], 5),
            "stdev_ms": round(variance ** 0.5, 5),
            "trials": row["count"],
        }
    return summary if summary else {"status": "Not measured"}


def export_csv(db) -> str:
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["algorithm", "operation", "input_size", "trial_number", "duration_ms", "payload_size", "timestamp", "environment"])
    for row in db.performance_results.find({}, {"_id": 0}):
        writer.writerow([row.get("algorithm"), row.get("operation"), row.get("input_size"),
                          row.get("trial_number"), row.get("duration_ms"), row.get("payload_size"),
                          row.get("timestamp"), row.get("environment")])
    return output.getvalue()
