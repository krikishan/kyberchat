import os

from flask import Blueprint, current_app, jsonify

from app.database.db import ping

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    db_healthy = ping()
    email_configured = bool(current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"))
    groq_configured = bool(current_app.config.get("GROQ_API_KEY"))

    services = {
        "backend_api": "healthy",
        "database": "healthy" if db_healthy else "unavailable",
        "email_service": "healthy" if email_configured else "not_configured",
        "groq_ai": "healthy" if groq_configured else "not_configured",
        "authentication": "healthy",
    }
    overall = "healthy" if all(v in ("healthy",) for v in [services["backend_api"], services["database"], services["authentication"]]) else "warning"

    return jsonify({"overall_status": overall, "services": services})
