from datetime import date
from decimal import Decimal

from flask import jsonify, request
from sqlalchemy import select

from db_connection import session
from hotels import hotels_bp
from models import Hotel, HotelAmenity, HotelPhoto, HotelRoom, Review


def _parse_iso_date(value, field_name):
    if not value:
        return None, f"{field_name} is required"

    try:
        return date.fromisoformat(value), None
    except ValueError:
        return None, f"{field_name} must be a valid date in YYYY-MM-DD format"


def _serialize_decimal(value):
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


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


@hotels_bp.route("/<int:hotel_id>", methods=["GET"])
def get_hotel_details(hotel_id):
    hotel = session.get(Hotel, hotel_id)
    if hotel is None:
        return jsonify({"error": "Hotel not found"}), 404

    room_stmt = (
        select(HotelRoom)
        .where(HotelRoom.hotel == hotel_id)
        .order_by(HotelRoom.room.asc())
    )
    photo_stmt = (
        select(HotelPhoto)
        .where(HotelPhoto.hotel_id == hotel_id)
        .order_by(HotelPhoto.id.asc())
    )
    amenity_stmt = (
        select(HotelAmenity)
        .where(HotelAmenity.hotel_id == hotel_id)
        .order_by(HotelAmenity.name.asc())
    )
    review_stmt = (
        select(Review)
        .where(Review.hotel == hotel_id)
        .order_by(Review.id.desc())
    )

    rooms = session.execute(room_stmt).scalars().all()
    photos = session.execute(photo_stmt).scalars().all()
    amenities = session.execute(amenity_stmt).scalars().all()
    reviews = session.execute(review_stmt).scalars().all()

    room_type_summary = {}
    for room in rooms:
        room_type_name = room.room_type.value
        if room_type_name not in room_type_summary:
            room_type_summary[room_type_name] = {
                "type": room_type_name,
                "count": 0,
                "room_numbers": [],
            }
        room_type_summary[room_type_name]["count"] += 1
        room_type_summary[room_type_name]["room_numbers"].append(room.room)

    return jsonify(
        {
            "id": hotel.id,
            "name": hotel.name,
            "city": hotel.city,
            "address": hotel.address,
            "price_per_night": _serialize_decimal(hotel.price_per_night),
            "rating": _serialize_decimal(hotel.rating),
            "photos": [
                {
                    "id": photo.id,
                    "url": photo.url,
                    "alt_text": photo.alt_text,
                }
                for photo in photos
            ],
            "room_types": list(room_type_summary.values()),
            "amenities": [amenity.name for amenity in amenities],
            "reviews": [
                {
                    "id": review.id,
                    "user_id": review.user,
                    "title": review.title,
                    "content": review.content,
                    "rating": review.rating,
                }
                for review in reviews
            ],
        }
    ), 200
