import os
from flask import Flask
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from backend.extensions import bcrypt

load_dotenv()


def _env_flag(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def create_app():
    app = Flask(__name__)
    debug_enabled = _env_flag("FLASK_DEBUG", False)
    app.config["JWT_SECRET_KEY"] = os.environ.get(
        "JWT_SECRET_KEY",
        os.environ.get("SECRET_KEY", "likehome-dev-secret-change-in-prod"),
    )
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
    # Empty string means Google OAuth is disabled — the frontend hides the button
    app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID", "")
    app.config["FRONTEND_BASE_URL"] = os.environ.get(
        "FRONTEND_BASE_URL", "http://localhost:5173"
    )
    app.config["PASSWORD_RESET_TOKEN_TTL_SECONDS"] = int(
        os.environ.get("PASSWORD_RESET_TOKEN_TTL_SECONDS", "3600")
    )
    app.config["EXPOSE_RESET_TOKEN_IN_RESPONSE"] = _env_flag(
        "EXPOSE_RESET_TOKEN_IN_RESPONSE", False
    )
    app.config["SMTP_HOST"] = os.environ.get("SMTP_HOST", "")
    app.config["SMTP_PORT"] = int(os.environ.get("SMTP_PORT", "0"))
    app.config["SMTP_USERNAME"] = os.environ.get("SMTP_USERNAME", "")
    app.config["SMTP_PASSWORD"] = os.environ.get("SMTP_PASSWORD", "")
    app.config["SMTP_FROM_EMAIL"] = os.environ.get(
        "SMTP_FROM_EMAIL", os.environ.get("SMTP_USERNAME", "noreply@likehome.local")
    )
    app.config["SMTP_USE_TLS"] = _env_flag("SMTP_USE_TLS", True)
    app.config["SMTP_USE_SSL"] = _env_flag("SMTP_USE_SSL", False)

    bcrypt.init_app(app)
    JWTManager(app)

    # Register every blueprint with its URL prefix
    from backend.auth import auth_bp
    from backend.search import search_bp
    from backend.reservation import reservation_bp
    from backend.rewards import rewards_bp
    from backend.saved_searches import saved_search_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(search_bp, url_prefix="/hotels")
    app.register_blueprint(reservation_bp, url_prefix="/reservations")
    app.register_blueprint(rewards_bp, url_prefix="/rewards")
    app.register_blueprint(saved_search_bp, url_prefix="/saved-searches")

    return app
