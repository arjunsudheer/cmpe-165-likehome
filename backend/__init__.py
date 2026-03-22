import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from backend.auth import auth_bp
from backend.extensions import bcrypt
from backend.reservation import reservation_bp
from backend.search import search_bp

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "default-secret-key"),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "jwt-dev-secret"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID"),
    )

    CORS(app)
    JWTManager(app)
    bcrypt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(search_bp, url_prefix="/hotels")
    app.register_blueprint(reservation_bp, url_prefix="/reservations")
    return app
