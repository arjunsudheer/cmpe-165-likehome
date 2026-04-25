from datetime import date

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func, select

from backend.db.db_connection import session
from backend.db.models import Hotel, HotelAmenity, HotelPhoto, HotelRoom, Review, User, SavedSearch
from backend.search import search_bp


def _f(val):
    return float(val) if val is not None else 0.0


def _hotel_summary(hotel):
    """Build a card-ready summary: one photo + amenities + review count."""
    photo = session.execute(
        select(HotelPhoto.url).where(HotelPhoto.hotel_id == hotel.id).limit(1)
    ).scalar()
    amenities = session.execute(
        select(HotelAmenity.name).where(HotelAmenity.hotel_id == hotel.id)
    ).scalars().all()
    review_count = session.execute(
        select(func.count(Review.id)).where(Review.hotel == hotel.id)
    ).scalar() or 0
    return {
        "id": hotel.id,
        "name": hotel.name,
        "city": hotel.city,
        "address": hotel.address,
        "price_per_night": _f(hotel.price_per_night),
        "rating": _f(hotel.rating),
        "review_count": int(review_count),
        "primary_photo": photo,
        "amenities": list(amenities),
    }

def _get_sort_clause():
    """
    Supported query params:
      ?sort=price&order=asc
      ?sort=price&order=desc
      ?sort=rating&order=asc
      ?sort=rating&order=desc
    Defaults to rating desc, then price asc.
    """
    sort_field = request.args.get("sort_field") or request.args.get("sort")
    if not sort_field:
        sort_field = "rating"
    sort_field = sort_field.strip().lower()
    
    sort_order = request.args.get("sort_order") or request.args.get("order")
    if not sort_order:
        sort_order = "desc"
    sort_order = sort_order.strip().lower()

    valid_fields = {"price", "rating"}
    valid_orders = {"asc", "desc"}

    if sort_field not in valid_fields:
        sort_field = "rating"
    if sort_order not in valid_orders:
        sort_order = "desc"

    if sort_field == "price":
        primary = (
            Hotel.price_per_night.asc()
            if sort_order == "asc"
            else Hotel.price_per_night.desc()
        )
        secondary = Hotel.rating.desc()
    else:
        primary = Hotel.rating.asc() if sort_order == "asc" else Hotel.rating.desc()
        secondary = Hotel.price_per_night.asc()

    return [primary, secondary]


def refresh_hotel_rating(hotel_id):
    avg = session.execute(
        select(func.avg(Review.rating)).where(Review.hotel == hotel_id)
    ).scalar()
    hotel = session.get(Hotel, hotel_id)
    if hotel is None:
        return None
    rating = round(float(avg or 0), 2)
    hotel.rating = rating
    session.commit()
    return rating


@search_bp.route("/", methods=["GET"])
def get_all_hotels():
    """Default homepage view — all hotels ordered by rating."""
    sort_clause = _get_sort_clause()
    hotels = session.execute(select(Hotel).order_by(*sort_clause)).scalars().all()
    return jsonify({"results": [_hotel_summary(h) for h in hotels]}), 200


@search_bp.route("/search", methods=["GET"])
def search_hotels():
    destination = request.args.get("destination", "").strip()
    check_in_raw = request.args.get("check_in")
    check_out_raw = request.args.get("check_out")
    saved_search_id = request.args.get("saved_search_id") or None

    filters = {}
    if saved_search_id:
        saved_search = session.execute(select(SavedSearch).where(SavedSearch.id==saved_search_id)).scalar_one_or_none()
        destination = saved_search.destination
        check_in_raw = date.isoformat(saved_search.check_in)
        check_out_raw = date.isoformat(saved_search.check_out)
        filters = saved_search.filters

    if not destination:
        return jsonify({"error": "destination is required"}), 400
    try:
        check_in = date.fromisoformat(check_in_raw)
        check_out = date.fromisoformat(check_out_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "Dates must be YYYY-MM-DD"}), 400

    if check_in < date.today():
        return jsonify({"error": "check_in cannot be in the past"}), 400
    if check_out <= check_in:
        return jsonify({"error": "check_out must be after check_in"}), 400

    sort_clause = _get_sort_clause()
    hotels = session.execute(
        select(Hotel)
        .where(Hotel.city.ilike(f"%{destination}%"))
        .order_by(*sort_clause)
    ).scalars().all()

    return jsonify({
        "destination": destination,
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "results": [_hotel_summary(h) for h in hotels],
        "filters": filters or {}
    }), 200


@search_bp.route("/<int:hotel_id>", methods=["GET"])
def get_hotel_details(hotel_id):
    hotel = session.get(Hotel, hotel_id)
    if hotel is None:
        return jsonify({"error": "Hotel not found"}), 404

    photos = session.execute(
        select(HotelPhoto).where(HotelPhoto.hotel_id == hotel_id).order_by(HotelPhoto.id)
    ).scalars().all()
    amenities = session.execute(
        select(HotelAmenity).where(HotelAmenity.hotel_id == hotel_id).order_by(HotelAmenity.name)
    ).scalars().all()
    reviews = session.execute(
        select(Review).where(Review.hotel == hotel_id).order_by(Review.id.desc())
    ).scalars().all()
    rooms = session.execute(
        select(HotelRoom).where(HotelRoom.hotel == hotel_id)
    ).scalars().all()

    # Group rooms by type for display
    room_types: dict = {}
    for r in rooms:
        t = r.room_type.value
        if t not in room_types:
            room_types[t] = {"type": t, "count": 0}
        room_types[t]["count"] += 1

    avg = _f(hotel.rating)
    return jsonify({
        "id": hotel.id,
        "name": hotel.name,
        "city": hotel.city,
        "address": hotel.address,
        "price_per_night": _f(hotel.price_per_night),
        "rating": avg,
        "review_count": len(reviews),
        "photos": [{"id": p.id, "url": p.url, "alt_text": p.alt_text} for p in photos],
        "amenities": [a.name for a in amenities],
        "room_types": list(room_types.values()),
        "reviews": [
            {
                "id": r.id,
                "user_id": r.user,
                "title": r.title,
                "content": r.content,
                "rating": r.rating,
            }
            for r in reviews
        ],
    }), 200


@search_bp.route("/<int:hotel_id>/reviews", methods=["POST"])
@jwt_required()
def create_review(hotel_id):
    if session.get(Hotel, hotel_id) is None:
        return jsonify({"error": "Hotel not found"}), 404

    user_id = int(get_jwt_identity())
    if not session.get(User, user_id):
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    rating = data.get("rating")

    if not isinstance(rating, int) or not 1 <= rating <= 5:
        return jsonify({"error": "rating must be integer 1–5"}), 400

    review = Review(
        user=user_id,
        hotel=hotel_id,
        title=data.get("title", "No title"),
        content=data.get("content", "No content"),
        rating=rating,
    )
    session.add(review)
    session.commit()
    new_rating = refresh_hotel_rating(hotel_id)
    return jsonify({"message": "Review created", "hotel_rating": new_rating}), 201
