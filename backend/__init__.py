import os
from flask import Flask
from flask_jwt_extended import JWTManager
from backend.extensions import bcrypt


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.environ.get(
        "JWT_SECRET_KEY", "likehome-dev-secret-change-in-prod"
    )
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
    # Empty string means Google OAuth is disabled — the frontend hides the button
    app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID", "")

    bcrypt.init_app(app)
    JWTManager(app)

    # Register every blueprint with its URL prefix
    from backend.auth import auth_bp
    from backend.search import search_bp
    from backend.reservation import reservation_bp
    from backend.rewards import rewards_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(search_bp, url_prefix="/hotels")
    app.register_blueprint(reservation_bp, url_prefix="/reservations")
    app.register_blueprint(rewards_bp, url_prefix="/rewards")

    return app
