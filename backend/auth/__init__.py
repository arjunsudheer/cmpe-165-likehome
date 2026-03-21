# create auth blueprint

from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

# import routes after registering blueprint to avoid circular imports
import backend.auth.routes
