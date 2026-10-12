import os


class Config:
    ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = ENV == "development"

    SECRET_KEY = os.environ["SECRET_KEY"]
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    JWT_ACCESS_TOKEN_EXPIRES_MIN = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MIN", "60"))

    MONGODB_URI = os.environ["MONGODB_URI"]
    MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "kyberchat")

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")  # optional: AI enhancer degrades gracefully

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:5000")

    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB request/file size cap
    BULK_ADD_MAX_BATCH = 50
    AI_ENHANCE_MAX_INPUT_CHARS = 2000


def load_config():
    """Fail fast and loudly if a required secret is missing, instead of
    silently running with an insecure default."""
    required = ["SECRET_KEY", "JWT_SECRET_KEY", "MONGODB_URI"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in real values."
        )
    return Config
