# for creating flask app and registering all blueprints

import os
from flask import Flask
from flask_cors import CORS

from backend.auth import auth_bp
from backend.extensions import bcrypt


def create_app():
    app = Flask(__name__)

    # configurations
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "default-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID"),
    )

    CORS(app)  # enable CORS for all routes

    bcrypt.init_app(app)  # initialize bcrypt
    app.register_blueprint(auth_bp, url_prefix="/auth")  # auth bp

    return app
