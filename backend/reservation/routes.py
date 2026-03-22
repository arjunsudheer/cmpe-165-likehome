import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from backend.db.db_connection import engine
from backend.db.models import Booking, HotelRoom, Hotel, Status


def generate_booking_number():
    return "LH-" + uuid.uuid4().hex[:8].upper()


def check_room_availability(session, room_id, start_date, end_date, exclude_booking_id=None):
    stmt = select(Booking).where(
        and_(
            Booking.room == room_id,
            Booking.status != Status.CANCELLED,
            Booking.start_date < end_date,
            Booking.end_date > start_date,
        )
    )
    if exclude_booking_id:
        stmt = stmt.where(Booking.id != exclude_booking_id)
    return session.execute(stmt).scalars().all()


def calculate_total_price(price_per_night, start_date, end_date):
    nights = (end_date - start_date).days
    return Decimal(str(price_per_night)) * nights


from backend.reservation import reservation_bp


@reservation_bp.route("/", methods=["GET"])
@jwt_required()
def list_bookings():
    user_id = get_jwt_identity()
    with Session(engine) as session:
        stmt = (
            select(Booking)
            .where(Booking.user == user_id)
            .order_by(Booking.created_at.desc())
        )
        bookings = session.execute(stmt).scalars().all()
        return jsonify([
            {
                "id": b.id,
                "booking_number": b.booking_number,
                "title": b.title,
                "room": b.room,
                "start_date": b.start_date.isoformat(),
                "end_date": b.end_date.isoformat(),
                "total_price": str(b.total_price),
                "status": b.status.value,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bookings
        ]), 200


@reservation_bp.route("/", methods=["POST"])
@jwt_required()
def create_booking():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    title = data.get("title")
    room_id = data.get("room")
    start_str = data.get("start_date")
    end_str = data.get("end_date")

    if not all([title, room_id, start_str, end_str]):
        return jsonify({"error": "title, room, start_date, and end_date are required"}), 400

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Dates must be in YYYY-MM-DD format"}), 400

    if end_date <= start_date:
        return jsonify({"error": "end_date must be after start_date"}), 400

    if start_date < date.today():
        return jsonify({"error": "start_date cannot be in the past"}), 400

    with Session(engine) as session:
        room = session.execute(
            select(HotelRoom).where(HotelRoom.id == room_id).with_for_update()
        ).scalar_one_or_none()
        if not room:
            return jsonify({"error": "Room not found"}), 404

        hotel = session.execute(
            select(Hotel).where(Hotel.id == room.hotel)
        ).scalar_one_or_none()
        if not hotel:
            return jsonify({"error": "Hotel not found"}), 404

        conflicts = check_room_availability(session, room_id, start_date, end_date)
        if conflicts:
            return jsonify({
                "error": "Room is not available for the selected dates",
                "conflicts": [
                    {
                        "booking_id": c.id,
                        "start_date": c.start_date.isoformat(),
                        "end_date": c.end_date.isoformat(),
                    }
                    for c in conflicts
                ],
            }), 409

        total_price = calculate_total_price(hotel.price_per_night, start_date, end_date)
        booking_number = generate_booking_number()

        booking = Booking(
            booking_number=booking_number,
            title=title,
            user=user_id,
            room=room_id,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price,
            status=Status.INPROGRESS,
            expires_at=datetime.now() + timedelta(minutes=15)
        )
        session.add(booking)
        session.commit()

        return jsonify({
            "message": "Booking in progress, confirm within 15 minutes",
            "booking": {
                "id": booking.id,
                "booking_number": booking.booking_number,
                "title": booking.title,
                "room": booking.room,
                "hotel_name": hotel.name,
                "start_date": booking.start_date.isoformat(),
                "end_date": booking.end_date.isoformat(),
                "total_price": str(booking.total_price),
                "status": booking.status.value,
                "expires_at": booking.expires_at.isoformat(),
            },
        }), 201
    
@reservation_bp.route("/<int:booking_id>/confirm", methods=["POST"])
@jwt_required()
def confirm_booking(booking_id):
    user_id = get_jwt_identity()
    with Session(engine) as session:
        booking = session.execute(
            select(Booking).where(
                and_(Booking.id == booking_id, Booking.user == user_id)
            )
        ).scalar_one_or_none()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking.status == Status.CANCELLED:
            return jsonify({"error": "Booking has expired or been cancelled"}), 400
        if booking.status == Status.CONFIRMED:
            return jsonify({"error": "Booking is already confirmed"}), 400
        if booking.expires_at < datetime.now():
            booking.status = Status.CANCELLED
            session.commit()
            return jsonify({"error": "Booking has expired"}), 400

        booking.status = Status.CONFIRMED
        booking.expires_at = None
        session.commit()

        return jsonify({
            "message": "Booking confirmed",
            "booking_number": booking.booking_number,
        }), 200


@reservation_bp.route("/<int:booking_id>", methods=["GET"])
@jwt_required()
def get_booking(booking_id):
    user_id = get_jwt_identity()
    with Session(engine) as session:
        booking = session.execute(
            select(Booking).where(
                and_(Booking.id == booking_id, Booking.user == user_id)
            )
        ).scalar_one_or_none()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        room = session.execute(
            select(HotelRoom).where(HotelRoom.id == booking.room)
        ).scalar_one_or_none()
        hotel = session.execute(
            select(Hotel).where(Hotel.id == room.hotel)
        ).scalar_one_or_none() if room else None

        return jsonify({
            "id": booking.id,
            "booking_number": booking.booking_number,
            "title": booking.title,
            "room": booking.room,
            "hotel_name": hotel.name if hotel else None,
            "start_date": booking.start_date.isoformat(),
            "end_date": booking.end_date.isoformat(),
            "total_price": str(booking.total_price),
            "status": booking.status.value,
            "created_at": booking.created_at.isoformat() if booking.created_at else None,
        }), 200


@reservation_bp.route("/<int:booking_id>", methods=["DELETE"])
@jwt_required()
def cancel_booking(booking_id):
    user_id = get_jwt_identity()
    with Session(engine) as session:
        booking = session.execute(
            select(Booking).where(
                and_(Booking.id == booking_id, Booking.user == user_id)
            )
        ).scalar_one_or_none()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking.status == Status.CANCELLED:
            return jsonify({"error": "Booking is already cancelled"}), 400

        booking.status = Status.CANCELLED
        session.commit()

        return jsonify({
            "message": "Booking cancelled",
            "booking_number": booking.booking_number,
        }), 200
