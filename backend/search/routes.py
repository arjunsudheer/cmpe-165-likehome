from datetime import date, timedelta
import random

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func, select, and_, or_, insert
import requests
from backend.search.api_params import hotel_list_url, headers, city_url, hotel_details_url, hotel_photos_url, BASE_API_URL
from dataclasses import dataclass, field

from backend.db.db_connection import session
from backend.db.models import Hotel, HotelAmenity, HotelPhoto, HotelRoom, Review, User, Booking, Status, SavedSearch, RoomType, CancellationPolicy
from backend.search import search_bp

@dataclass
class CachedHotel:
    name: str = ""
    city: str = ""
    price_per_night: float = 0.0
    primary_photo: str = ""
    address: str = ""
    amenities: list = field(default_factory=list)
    reviews: list = field(default_factory=list)
    rooms: list = field(default_factory=list)
    photos: list = field(default_factory=list)
    cancellation_policy: list = field(default_factory=list)

_hotel_details_cache: dict[int, CachedHotel] = {}

amenity_sets = [
    ["Free WiFi", "Pool", "Fitness Center", "Parking", "Breakfast Included"],
    ["Free WiFi", "Spa", "Airport Shuttle", "Restaurant", "Pet Friendly"],
    ["Free WiFi", "Beach Access", "Bar", "Parking", "Family Rooms"],
    ["Free WiFi", "Business Center", "Room Service", "Gym", "Laundry Service"]
  ]

def _f(val):
    return float(val) if val is not None else 0.0


def _as_float(name: str, default: float | None = None):
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None

def _mock_hotel_details_for_preview(hotel_id):
    cached = _hotel_details_cache.get(hotel_id)
    if cached and cached.amenities and cached.reviews:
        return {"amenities": cached.amenities, "reviews": cached.reviews}

    rng = random.Random(hotel_id)
    amenity_set = rng.choice(amenity_sets)

    user_ids = session.execute(select(User.id)).scalars().all()
    if not user_ids:
        for index in range(1, 6):
            session.execute(
                insert(User).values(
                    email=f"reviewer{index}@example.com",
                    password="seeded-password",
                )
            )
        user_ids = session.execute(select(User.id)).scalars().all()
        session.commit()

    reviews = []
    for review_offset in range(2):
        user_id = rng.choice(user_ids)
        reviews.append({
                "user":user_id,
                "hotel":hotel_id,
                "title":f"Guest review {review_offset + 1}",
                "content":f"Comfortable stay at hotel {hotel_id}.",
                "rating":4 if review_offset == 0 else 5,
            }
        )

    _hotel_details_cache.setdefault(hotel_id, CachedHotel()).amenities = amenity_set
    _hotel_details_cache[hotel_id].reviews = reviews
    return {
        "amenities": amenity_set,
        "reviews": reviews
    }

def _mock_hotel_details_for_individual_page(hotel_id):
    cached = _hotel_details_cache.get(hotel_id)
    if cached and cached.rooms and cached.photos and cached.cancellation_policy:
        return {"rooms": cached.rooms, "photos": cached.photos, "cancellation_policy": cached.cancellation_policy}
    rng = random.Random(hotel_id)

    rooms = []
    for room_number in range(1, rng.randint(6, 26)):
        rooms.append({
            "hotel":hotel_id,
            "room":room_number,
            "room_type":rng.choice([e.value for e in RoomType]),
        })

    querystring = {"languagecode":"en-us","hotel_ids":hotel_id}
    response = _api_response(hotel_photos_url, querystring)

    photos = []
    hotel_photos_response = response.get('data', {}).get(str(hotel_id))
    url_prefix = response.get('url_prefix')
    if hotel_photos_response:
        for photo in hotel_photos_response:
            url = url_prefix + photo[4]
            tag = photo[3][0].get('tag') if photo[3] and len(photo[3]) > 0 else ""
            photos.append({
                    "hotel_id":hotel_id,
                    "url":url,
                    "alt_text":tag
                }
            )

    cancellation_policy = {"hotel_id": hotel_id, "deadline_hours": 48, "fee_percent": 0, "active": True}

    _hotel_details_cache.setdefault(hotel_id, CachedHotel()).rooms = rooms
    _hotel_details_cache[hotel_id].photos = photos
    _hotel_details_cache[hotel_id].cancellation_policy = cancellation_policy
    return {"rooms": rooms, "photos": photos, "cancellation_policy": cancellation_policy}

def _api_response(endpoint, params):
    return requests.get(url=f"{BASE_API_URL}{endpoint}", headers=headers, params=params).json()

def _hotel_summary(hotel):
    """Build a card-ready summary: one photo + amenities + review count."""
    hotel_id = hotel.get('hotel_id')
    existing_hotel = _hotel_details_cache.setdefault(hotel_id, CachedHotel())
    if not existing_hotel.amenities or not existing_hotel.reviews:
        result = _mock_hotel_details_for_preview(hotel_id)
        amenities = result.get('amenities')
        reviews = result.get('reviews')
    else:
        amenities = existing_hotel.amenities
        reviews = existing_hotel.reviews

    # load/refresh the hotel values
    name = existing_hotel.name = hotel.get("hotel_name") or existing_hotel.name
    city = existing_hotel.city = hotel.get("city") or existing_hotel.city
    breakdown = hotel.get('composite_price_breakdown') or {}
    per_night = breakdown.get('gross_amount_per_night') or {}
    price_per_night = existing_hotel.price_per_night = _f(per_night.get('value'))
    primary_photo = existing_hotel.primary_photo = (hotel.get('main_photo_url') or '').replace('square60', 'max1280x900') or existing_hotel.primary_photo
    
    review_count = len(reviews)
    rating = sum(review["rating"] for review in reviews) / review_count if review_count != 0 else 0.0
    _hotel_details_cache[hotel_id].rating = rating

    return {
        "id": hotel.get('hotel_id'),
        "name": name,
        "city": city,
        "price_per_night": price_per_night,
        "rating": _f(rating),
        "review_count": int(review_count),
        "primary_photo": primary_photo,
        "amenities": amenities
    }

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
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    next_date = (date.today() + timedelta(days=10)).isoformat()

    # Home page defaults to a search for hotels in San Jose with 1 guest within the next 10 days, sorted by popularity
    querystring = {
        "offset": "0",
        "arrival_date": tomorrow,
        "departure_date": next_date,
        "guest_qty": "1",
        "dest_ids": "20015742",  
        "room_qty": "1",
        "search_type": "city;hotel",
        "price_filter_currencycode": "USD",
        "languagecode": "en-us",
    }

    response = _api_response(hotel_list_url, querystring)
    hotels = [h for h in response.get("result", []) if h.get("type") == "property_card" and h.get("soldout") == 0]


    return jsonify({"dest_ids": "20015742", "check_in": tomorrow,
        "check_out": next_date,
        "guests": "1",
        "search_id": response.get('search_id'),"results": [_hotel_summary(h) for h in hotels],
        }), 200


@search_bp.route("/search", methods=["GET"])
def search_hotels():
    destination = request.args.get("destination", "").strip()
    check_in_raw = request.args.get("check_in")
    check_out_raw = request.args.get("check_out")
    guests = request.args.get("guests")
    saved_search_id = request.args.get("saved_search_id") or None

    filters = {}
    if saved_search_id:
        saved_search = session.execute(select(SavedSearch).where(SavedSearch.id==saved_search_id)).scalar_one_or_none()
        destination = saved_search.destination
        check_in_raw = saved_search.check_in.isoformat()
        check_out_raw = saved_search.check_out.isoformat()
        filters = saved_search.filters
        guests = str(saved_search.guests)

    if not destination:
        return jsonify({"error": "destination is required"}), 400
    if not guests:
        return jsonify({"error": "guests is required"}), 400
    try:
        check_in = date.fromisoformat(check_in_raw)
        check_out = date.fromisoformat(check_out_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "Dates must be YYYY-MM-DD"}), 400

    if check_in < date.today():
        return jsonify({"error": "check_in cannot be in the past"}), 400
    if check_out <= check_in:
        return jsonify({"error": "check_out must be after check_in"}), 400

    city = {"languagecode":"en-us","text":destination}

    destinations_response = _api_response(city_url, city)
    if not destinations_response:
        return jsonify({"error": "No destinations found"}), 404

    destination_ids = [str(location.get("dest_id")) for location in destinations_response]

    querystring = {"offset":"0","arrival_date":check_in_raw,"departure_date":check_out_raw,"guest_qty":guests,"dest_ids":destination_ids,"room_qty":"1","search_type":"city; hotel","price_filter_currencycode":"USD","languagecode":"en-us"}

    hotels_response = _api_response(hotel_list_url, querystring)
    hotels = [h for h in hotels_response.get("result", []) if h.get("type") == "property_card" and h.get("soldout") == 0]

    return jsonify({
        "destination": destination,
        "dest_ids": destination_ids,
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "guests": guests,
        "search_id": hotels_response.get('search_id'),
        "results": [_hotel_summary(h) for h in hotels],
        "filters": filters or {}
    }), 200


@search_bp.route("/geocode", methods=["GET"])
def geocode_location():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "q is required"}), 400

    try:
        res = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"format": "json", "limit": 1, "q": query},
            headers={"Accept": "application/json", "User-Agent": "likehome/1.0"},
            timeout=8,
        )
        if res.status_code != 200:
            return jsonify({"error": "Geocoding provider unavailable"}), 502
        data = res.json()
        if not data:
            return jsonify({"result": None}), 200

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return jsonify({"result": {"lat": lat, "lon": lon}}), 200
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return jsonify({"error": "Failed to geocode location"}), 502


@search_bp.route("/nearby", methods=["GET"])
def nearby_places():
    lat = _as_float("lat")
    lon = _as_float("lon")
    radius = _as_float("radius", 1200.0)
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required numeric query params"}), 400
    if radius is None or radius <= 0:
        return jsonify({"error": "radius must be a positive number"}), 400

    overpass_query = f"""
[out:json][timeout:12];
(
  node["amenity"="restaurant"](around:{int(radius)},{lat},{lon});
  node["amenity"="fuel"](around:{int(radius)},{lat},{lon});
);
out body;"""
    try:
        res = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=overpass_query,
            headers={"Accept": "application/json", "User-Agent": "likehome/1.0"},
            timeout=12,
        )
        if res.status_code != 200:
            return jsonify({"error": "Nearby provider unavailable"}), 502
        data = res.json()
        return jsonify({"elements": data.get("elements", [])}), 200
    except (requests.RequestException, ValueError, TypeError):
        return jsonify({"error": "Failed to load nearby places"}), 502


@search_bp.route("/<int:hotel_id>", methods=["GET"])
def get_hotel_details(hotel_id):
    dest_ids = request.args.get("dest_ids", "").strip()
    check_in_raw = request.args.get("check_in") or (date.today() + timedelta(days=1)).isoformat()
    check_out_raw = request.args.get("check_out") or (date.today() + timedelta(days=10)).isoformat()
    guests = request.args.get("guests") or "1"
    search_id = request.args.get("search_id") or ""

    if hotel_id not in _hotel_details_cache:
        _hotel_details_cache[hotel_id] = CachedHotel()
    hotel =  _hotel_details_cache[hotel_id]
    if not hotel.rooms or not hotel.photos:
        result = _mock_hotel_details_for_individual_page(hotel_id)
        hotel.rooms = result.get('rooms')
        hotel.photos = result.get('photos')
    rooms = hotel.rooms
    photos = hotel.photos
    
    querystring = {"dest_ids": dest_ids, "hotel_id":hotel_id,"search_id":search_id,"departure_date":check_out_raw,"arrival_date":check_in_raw,"rec_guest_qty":guests,"rec_room_qty":"1","languagecode":"en-us","currency_code":"USD"}
    response = _api_response(hotel_details_url, querystring)
    hotel.address = response[0].get('address') if response else None

    # Group rooms by type for display
    room_types: dict = {}
    for r in rooms:
        t = r["room_type"]
        if t not in room_types:
            room_types[t] = {"type": t, "count": 0}
        room_types[t]["count"] += 1

    avg = _f(sum(review['rating'] for review in hotel.reviews) / len(hotel.reviews)) if hotel.reviews else 0.0
    _hotel_details_cache[hotel_id].rating = avg
    return jsonify({
        "id": hotel_id,
        "name": hotel.name,
        "city": hotel.city,
        "address": hotel.address,
        "price_per_night": _f(hotel.price_per_night),
        "rating": avg,
        "review_count": len(hotel.reviews),
        "photos": [{"url": p["url"], "alt_text": p["alt_text"]} for p in photos],
        "amenities": hotel.amenities,
        "room_types": list(room_types.values()),
        "reviews": [
            {
                "user_id": r["user"],
                "title": r["title"],
                "content": r["content"],
                "rating": r["rating"],
            }
            for r in hotel.reviews
        ],
    }), 200


@search_bp.route("/<int:hotel_id>/reviews", methods=["POST"])
@jwt_required()
def create_review(hotel_id):
    if _hotel_details_cache.get(hotel_id) is None:
        return jsonify({"error": "Hotel not found"}), 404

    user_id = int(get_jwt_identity())
    if not session.get(User, user_id):
        return jsonify({"error": "User not found"}), 404

    stayed = session.execute(
        select(Booking).where(
            and_(
                Booking.user == user_id,
                Booking.room.in_(select(HotelRoom.id).where(HotelRoom.hotel == hotel_id)),
                Booking.status == Status.COMPLETED
            )
        )
    ).scalar_one_or_none()

    if not stayed:
        return jsonify({"error": "You may only review hotels that you have stayed at."}), 403

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
    if session.get(Hotel, hotel_id):
        session.add(review)
        session.commit()
        new_rating = refresh_hotel_rating(hotel_id)
    else:
        _hotel_details_cache[hotel_id].reviews.append({
        "user":user_id,
        "hotel":hotel_id,
        "title":data.get("title", "No title"),
        "content":data.get("content", "No content"),
        "rating":rating})
        new_rating = sum(r['rating'] for r in _hotel_details_cache[hotel_id].reviews) / len(_hotel_details_cache[hotel_id].reviews) if len(_hotel_details_cache[hotel_id].reviews) else 0.0
    return jsonify({"message": "Review created", "hotel_rating": new_rating}), 201


@search_bp.route("/<int:hotel_id>/reviews/<int:review_id>", methods=["PATCH"])
@jwt_required()
def edit_review(hotel_id, review_id):
    user_id = int(get_jwt_identity())

    data = request.get_json(silent=True) or {}
    rating = data.get("rating")
    title = data.get("title")
    content = data.get("content")

    if rating is not None:
        if not isinstance(rating, int) or not 1 <= rating <= 5:
            return jsonify({"error": "rating must be integer 1–5"}), 400
    if title is not None:
        if len(title) > 20 or not title.strip():
            return jsonify({"error": "Title must be 20 characters or fewer"}), 400
    if content is not None:
        if len(content) > 255 or not content.strip():
            return jsonify({"error": "Content must be 255 characters or fewer"}), 400

    review = session.get(Review, review_id)
    if review:
        if review.hotel != hotel_id:
            return jsonify({"error": "Review does not belong to this hotel"}), 404
        if review.user != user_id:
            return jsonify({"error": "You can only edit your own reviews"}), 403

        if rating is not None:
            review.rating = rating
        if title is not None:
            review.title = title.strip()
        if content is not None:
            review.content = content.strip()
        session.commit()
        new_rating = refresh_hotel_rating(hotel_id)

    # update cache anyway regardless of whether review was in DB or not
    cached = _hotel_details_cache.get(hotel_id)
    if not cached:
        return jsonify({"error": "Hotel not found"}), 404

    cache_review = next((r for r in cached.reviews if r.get("id") == review_id), None)
    if not cache_review:
        return jsonify({"error": "Review not found"}), 404
    if cache_review.get("user") != user_id:
        return jsonify({"error": "You can only edit your own reviews"}), 403

    if rating is not None:
        cache_review["rating"] = rating
    if title is not None:
        cache_review["title"] = title.strip()
    if content is not None:
        cache_review["content"] = content.strip()

    new_rating = sum(r["rating"] for r in cached.reviews) / len(cached.reviews)
    return jsonify({
        "message": "Review updated",
        "review": {
            "id": review_id,
            "title": cache_review["title"],
            "content": cache_review["content"],
            "rating": cache_review["rating"],
        },
        "hotel_rating": new_rating,
    }), 200


@search_bp.route("/<int:hotel_id>/reviews/<int:review_id>", methods=["DELETE"])
@jwt_required()
def delete_review(hotel_id, review_id):
    user_id = int(get_jwt_identity())
    review = session.get(Review, review_id)
    if review:
        if review.hotel != hotel_id:
            return jsonify({"error": "Review does not belong to this hotel"}), 404
        if review.user != user_id:
            return jsonify({"error": "You can only delete your own reviews"}), 403

        session.delete(review)
        session.commit()
        new_rating = refresh_hotel_rating(hotel_id)

    # update cache anyway regardless of whether review was in DB or not
    cached = _hotel_details_cache.get(hotel_id)
    if not cached:
        return jsonify({"error": "Hotel not found"}), 404

    cache_review = next((r for r in cached.reviews if r.get("id") == review_id), None)
    if not cache_review:
        return jsonify({"error": "Review not found"}), 404
    if cache_review.get("user") != user_id:
        return jsonify({"error": "You can only delete your own reviews"}), 403

    cached.reviews = [r for r in cached.reviews if r.get("id") != review_id]
    new_rating = sum(r["rating"] for r in cached.reviews) / len(cached.reviews) if cached.reviews else 0.0
    return jsonify({
        "message": "Review deleted",
        "hotel_rating": new_rating,
    }), 200
