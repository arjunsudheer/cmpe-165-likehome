from flask import Blueprint

reservation_bp = Blueprint("reservation", __name__)

import backend.reservation.routes
