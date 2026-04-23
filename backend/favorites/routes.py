from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.db_connection import engine
from backend.db.models import Favorite, Hotel
from backend.favorites import favorites_bp


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
            return jsonify({"error": "Hotel not found"}), 404

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
