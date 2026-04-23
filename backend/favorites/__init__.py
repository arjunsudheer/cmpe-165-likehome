from flask import Blueprint

favorites_bp = Blueprint("favorites", __name__)

import backend.favorites.routes  # noqa: E402,F401
