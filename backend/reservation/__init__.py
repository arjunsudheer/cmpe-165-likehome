from flask import Blueprint

reservation_bp = Blueprint("reservation", __name__)

import backend.reservation.routes  # noqa: E402,F401  # pylint: disable=wrong-import-position,unused-import
