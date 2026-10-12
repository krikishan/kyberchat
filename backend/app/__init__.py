from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import load_config
from app.database.db import init_db

limiter = Limiter(key_func=get_remote_address)


def create_app(db_override=None):
    """db_override lets tests inject mongomock instead of a real MongoDB
    Atlas connection — production/dev callers should never pass this."""
    app = Flask(__name__)
    config = load_config()
    app.config.from_object(config)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    if db_override is not None:
        app.db = db_override
        from app.database import db as db_module
        db_module._db = db_override
        db_module.ping = lambda: True
    else:
        init_db(app)

    if app.config.get("GROQ_API_KEY"):
        try:
            from groq import Groq
            app.groq_client = Groq(api_key=app.config["GROQ_API_KEY"])
        except Exception:
            app.groq_client = None
    else:
        app.groq_client = None

    CORS(
        app,
        origins=[app.config["FRONTEND_URL"]],
        supports_credentials=True,
    )
    limiter.init_app(app)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        if app.config["ENV"] != "development":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

    @app.errorhandler(Exception)
    def handle_uncaught(e):
        app.logger.exception("Unhandled error")  # server-side only, never in response
        return jsonify({"error": "Service temporarily unavailable."}), 500

    from app.routes.auth_routes import auth_bp
    from app.routes.health_routes import health_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.conversation_routes import conversation_bp
    from app.routes.group_routes import group_bp
    from app.routes.file_routes import file_bp
    from app.routes.ai_routes import ai_bp
    from app.routes.crypto_routes import crypto_bp
    from app.routes.performance_routes import performance_bp
    from app.routes.team_routes import team_bp
    from app.routes.preferences_routes import preferences_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(conversation_bp, url_prefix="/api/conversations")
    app.register_blueprint(group_bp, url_prefix="/api/groups")
    app.register_blueprint(file_bp, url_prefix="/api/files")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(crypto_bp, url_prefix="/api/crypto")
    app.register_blueprint(performance_bp, url_prefix="/api/performance")
    app.register_blueprint(team_bp, url_prefix="/api/team")
    app.register_blueprint(preferences_bp, url_prefix="/api/preferences")

    return app
