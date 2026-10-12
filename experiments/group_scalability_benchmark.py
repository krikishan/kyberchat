"""
Group-scalability experiment (spec section 25). Measures REAL session
establishment (and rotation) time/payload size across group sizes, using an
in-process mongomock database — no Flask server or real Atlas cluster
needed to produce real, non-fabricated timings of the actual crypto/db code.

Usage:
    python experiments/group_scalability_benchmark.py --sizes 2,4,8,16,32 --trials 5
"""
import argparse
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("SECRET_KEY", "benchmark-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "benchmark-jwt-secret-key")
os.environ.setdefault("MONGODB_URI", "mongodb://unused")

import mongomock  # noqa: E402

from app.crypto.key_directory import generate_and_store_user_keys  # noqa: E402
from app.crypto import session_manager  # noqa: E402

SECRET_KEY = "benchmark-secret-key"


def _stats(values):
    return {
        "avg_ms": round(statistics.mean(values), 4),
        "min_ms": round(min(values), 4),
        "max_ms": round(max(values), 4),
        "stdev_ms": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
    }


def run(sizes: list[int], trials: int) -> dict:
    results = {}

    for size in sizes:
        establish_times, join_times, remove_times, payload_sizes = [], [], [], []

        for _ in range(trials):
            client = mongomock.MongoClient()
            db = client["bench"]
            member_ids = [f"user-{i}" for i in range(size)]
            for uid in member_ids:
                generate_and_store_user_keys(db, SECRET_KEY, uid)

            t0 = time.perf_counter()
            session_manager.establish_session(db, SECRET_KEY, "group", "bench-group", member_ids)
            establish_times.append((time.perf_counter() - t0) * 1000)

            payload = sum(
                len(doc["kem_ciphertext"]) // 2 + len(doc["wrapped_ciphertext"]) // 2
                for doc in db.session_keys.find({"context_type": "group", "context_id": "bench-group"})
            )
            payload_sizes.append(payload)

            # Membership-change overhead: one join, one removal
            new_member = f"user-{size}"
            generate_and_store_user_keys(db, SECRET_KEY, new_member)
            t0 = time.perf_counter()
            session_manager.establish_session(db, SECRET_KEY, "group", "bench-group", member_ids + [new_member])
            join_times.append((time.perf_counter() - t0) * 1000)

            t0 = time.perf_counter()
            session_manager.establish_session(db, SECRET_KEY, "group", "bench-group", member_ids)
            remove_times.append((time.perf_counter() - t0) * 1000)

        results[f"group_size_{size}"] = {
            "session_establishment": _stats(establish_times),
            "membership_join_overhead": _stats(join_times),
            "membership_removal_overhead": _stats(remove_times),
            "avg_total_wrapped_payload_bytes": round(statistics.mean(payload_sizes), 1),
            "trials": trials,
        }

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=str, default="2,4,8,16,32")
    parser.add_argument("--trials", type=int, default=5)
    args = parser.parse_args()

    sizes = [int(s) for s in args.sizes.split(",")]
    output = run(sizes, args.trials)

    os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "results", "group_scalability_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(output, indent=2))
    print(f"\nSaved to {out_path}")
