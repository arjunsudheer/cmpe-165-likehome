#for creating flask app and registering all blueprints

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .auth import auth_bp


def create_app():
    app = Flask(__name__)

   #auth bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app