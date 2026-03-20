from datetime import date

from flask import jsonify, request
from sqlalchemy import select

from db_connection import session
from hotels import hotels_bp
from models import Hotel


def _parse_iso_date(value, field_name):
    if not value:
        return None, f"{field_name} is required"

    try:
        return date.fromisoformat(value), None
    except ValueError:
        return None, f"{field_name} must be a valid date in YYYY-MM-DD format"


@hotels_bp.route("/search", methods=["GET"])
def search_hotels():
    destination = request.args.get("destination", "").strip()
    check_in_raw = request.args.get("check_in")
    check_out_raw = request.args.get("check_out")

    if not destination:
        return jsonify({"error": "destination is required"}), 400

    check_in, error = _parse_iso_date(check_in_raw, "check_in")
    if error:
        return jsonify({"error": error}), 400

    check_out, error = _parse_iso_date(check_out_raw, "check_out")
    if error:
        return jsonify({"error": error}), 400

    today = date.today()
    if check_in < today:
        return jsonify({"error": "check_in cannot be in the past"}), 400

    if check_out <= check_in:
        return jsonify({"error": "check_out must be after check_in"}), 400

    stmt = (
        select(Hotel)
        .where(Hotel.city.ilike(f"%{destination}%"))
        .order_by(Hotel.rating.desc(), Hotel.price_per_night.asc(), Hotel.name.asc())
    )
    hotels = session.execute(stmt).scalars().all()

    return jsonify(
        {
            "destination": destination,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "results": [
                {
                    "id": hotel.id,
                    "name": hotel.name,
                    "city": hotel.city,
                    "address": hotel.address,
                    "price_per_night": float(hotel.price_per_night),
                    "rating": float(hotel.rating or 0),
                }
                for hotel in hotels
            ],
        }
    ), 200
