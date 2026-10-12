from flask import Blueprint, Response, jsonify, request

from app.auth.tokens import require_auth, require_role
from app.database.db import get_db
from app.services.performance_service import export_csv, get_summary, run_and_store

performance_bp = Blueprint("performance", __name__)


@performance_bp.route("", methods=["GET"])
@require_auth
@require_role("developer")
def get_performance():
    db = get_db()
    return jsonify(get_summary(db))


@performance_bp.route("/run", methods=["POST"])
@require_auth
@require_role("developer")
def run_benchmark():
    data = request.get_json(silent=True) or {}
    trials = min(max(int(data.get("trials", 10)), 1), 50)  # reasonable bound for a web request
    db = get_db()
    count = run_and_store(db, trials)
    return jsonify({"message": f"Ran {trials} trials.", "records_stored": count})


@performance_bp.route("/export", methods=["GET"])
@require_auth
@require_role("developer")
def export():
    db = get_db()
    csv_data = export_csv(db)
    return Response(csv_data, mimetype="text/csv",
                     headers={"Content-Disposition": "attachment; filename=performance_results.csv"})
