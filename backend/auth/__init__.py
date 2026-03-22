from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

import backend.auth.routes  # noqa: E402,F401
