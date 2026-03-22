from flask import Blueprint

search_bp = Blueprint("search", __name__)

import backend.search.routes  # noqa: E402,F401
