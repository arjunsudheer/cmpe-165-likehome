from flask import Blueprint

rewards_bp = Blueprint("rewards", __name__)

import backend.rewards.routes  # noqa: E402,F401
