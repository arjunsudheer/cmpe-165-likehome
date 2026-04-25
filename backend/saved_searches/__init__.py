from flask import Blueprint

saved_search_bp = Blueprint("saved_searches", __name__)

import backend.saved_searches.routes # noqa: E402,F401
