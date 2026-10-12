from flask import Blueprint, jsonify, request

from app.auth.tokens import require_auth, require_role
from app.services.crypto_simulation import run_simulation

crypto_bp = Blueprint("crypto", __name__)


@crypto_bp.route("/simulation", methods=["POST"])
@require_auth
@require_role("developer")
def simulation():
    data = request.get_json(silent=True) or {}
    sample_message = (data.get("message") or "send me the report tomorrow")[:500]
    result = run_simulation(sample_message)
    return jsonify(result)


@crypto_bp.route("/test", methods=["POST"])
@require_auth
@require_role("developer")
def self_test():
    """Quick pass/fail: runs the real ML-KEM -> HKDF -> AES-256-GCM chain
    once and confirms both parties derive the same key and recover the
    original plaintext. Same operations as the pytest integrity suite,
    exposed as an API for the admin dashboard."""
    result = run_simulation("cryptographic self-test message")
    return jsonify({"passed": result["success"]})
