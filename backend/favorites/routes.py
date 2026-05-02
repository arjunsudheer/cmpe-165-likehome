from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_, select, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.db_connection import engine
from backend.db.models import Favorite, Hotel, HotelAmenity, HotelPhoto, HotelRoom, Review, CancellationPolicy
from backend.favorites import favorites_bp
from backend.search.routes import _hotel_details_cache


@favorites_bp.route("/", methods=["GET"])
@jwt_required()
def list_favorites():
    user_id = int(get_jwt_identity())
    with Session(engine) as db:
        rows = db.execute(
            select(Favorite, Hotel)
            .join(Hotel, Favorite.hotel_id == Hotel.id)
            .where(Favorite.user_id == user_id)
        ).all()
        return jsonify([
            {
                "hotel_id": hotel.id,
                "name": hotel.name,
                "city": hotel.city,
                "price_per_night": str(hotel.price_per_night),
                "rating": str(hotel.rating),
            }
            for _fav, hotel in rows
        ]), 200


@favorites_bp.route("/<int:hotel_id>", methods=["POST"])
@jwt_required()
def add_favorite(hotel_id):
    user_id = int(get_jwt_identity())
    with Session(engine) as db:
        hotel = db.get(Hotel, hotel_id)
        if not hotel:
            cached = _hotel_details_cache.get(hotel_id)
            if not cached:
                return jsonify({"error": "Hotel not found"}), 404
            db.add(Hotel(id=hotel_id, name=cached["name"], city=cached["city"],
                         price_per_night=cached["price_per_night"], rating=cached["rating"]))
            db.commit()
            for amenity in cached.amenities:
                db.execute(insert(HotelAmenity).values(hotel_id=hotel_id, name=amenity))
            for room in cached.rooms:
                db.execute(insert(HotelRoom).values(hotel=hotel_id, room=room["room"], room_type=room["room_type"]))
            for photo in cached.photos:
                db.execute(insert(HotelPhoto).values(hotel_id=hotel_id, url=photo["url"], alt_text=photo["alt_text"]))
            for review in cached.reviews:
                db.execute(insert(Review).values(user=review["user"], hotel=hotel_id, title=review["title"], content=review["content"], rating=review["rating"]))
            db.execute(insert(CancellationPolicy).values(hotel_id=hotel_id, deadline_hours=cached.cancellation_policy["deadline_hours"], fee_percent=cached.cancellation_policy["fee_percent"], active=cached.cancellation_policy["active"]))
            db.commit()
            hotel = db.get(Hotel, hotel_id)

        db.add(Favorite(user_id=user_id, hotel_id=hotel_id))
        try:
            db.commit()
        except IntegrityError:
            return jsonify({"error": "Already in favorites"}), 409

        return jsonify({"message": "Added to favorites", "hotel_id": hotel_id}), 201


@favorites_bp.route("/<int:hotel_id>", methods=["DELETE"])
@jwt_required()
def remove_favorite(hotel_id):
    user_id = int(get_jwt_identity())
    with Session(engine) as db:
        fav = db.execute(
            select(Favorite).where(
                and_(Favorite.user_id == user_id, Favorite.hotel_id == hotel_id)
            )
        ).scalar_one_or_none()
        if not fav:
            return jsonify({"error": "Not in favorites"}), 404

        db.delete(fav)
        db.commit()
        return jsonify({"message": "Removed from favorites", "hotel_id": hotel_id}), 200
