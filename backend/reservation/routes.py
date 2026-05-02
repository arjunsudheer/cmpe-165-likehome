from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_, select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.db.db_connection import engine
from backend.db.models import (
    Booking, Hotel, HotelRoom, PointsTransaction, Status, User,
)
from backend.db.queries import get_overlapping_booking_dates, room_availability
from backend.reservation import reservation_bp
from backend.reservation.utils import (
    calculate_total_price,
    check_room_availability,
    get_cancellation_details,
    generate_booking_number,
    send_cancellation_email,
    send_receipt_email
)

POINTS_PER_DOLLAR = 10

def _reschedule_conflicts(db, room_id, booking_id, start_date, end_date):
    return [
        c for c in check_room_availability(db, room_id, start_date, end_date)
        if c.id != booking_id
    ]


def _pricing_summary(price_difference):
    if price_difference < 0:
        return {
            "adjustment_type": "refund",
            "amount": str(abs(price_difference)),
        }
    if price_difference > 0:
        return {
            "adjustment_type": "charge",
            "amount": str(price_difference),
        }
    return {
        "adjustment_type": "none",
        "amount": "0.00",
    }


def _cancellation_payload(booking, details, points_to_restore=0):
    fee_amount = details["fee_amount"]
    refund_amount = Decimal("0.00") if not booking.refundable else details["refund_amount"]
    fee_amount = booking.total_price if not booking.refundable else details["fee_amount"]
    return {
        "booking_id": booking.id,
        "booking_number": booking.booking_number,
        "status": booking.status.value,
        "policy_hours": details["policy_hours"],
        "fee_percent": str(details["fee_percent"]),
        "check_in_date": booking.start_date.isoformat(),
        "cutoff_at": details["cutoff_at"].isoformat(),
        "fee_amount": str(fee_amount),
        "refund_amount": str(refund_amount),
        "points_to_restore": 0 if not booking.refundable else int(points_to_restore),
        "summary": {
            "fee_message": f'Cancellation fee: ${details["fee_amount"]}',
            "refund_message": f'Refund amount: ${details["refund_amount"]}',
        },
    }


# ── User-level scheduling conflict check ─────────────────────────────────────

@reservation_bp.route("/check-conflicts", methods=["GET"])
@jwt_required()
def check_user_conflicts():
    """Return any of the user's bookings that overlap the requested dates."""
    user_id = int(get_jwt_identity())
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")

    if not start_str or not end_str:
        return jsonify({"error": "start_date and end_date are required"}), 400

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Dates must be YYYY-MM-DD"}), 400

    rows = get_overlapping_booking_dates(user_id, start_date, end_date)
    conflicts = []

    with Session(engine) as db:
        for booking_id, title, b_start, b_end in rows:
            booking = db.get(Booking, booking_id)
            if not booking or booking.status in (Status.CANCELLED, Status.INPROGRESS):
                continue
            room = db.get(HotelRoom, booking.room)
            hotel = db.get(Hotel, room.hotel) if room else None
            conflicts.append({
                "booking_id": booking_id,
                "title": title,
                "hotel_name": hotel.name if hotel else None,
                "start_date": b_start.isoformat(),
                "end_date": b_end.isoformat(),
            })

    return jsonify({"conflicts": conflicts}), 200


# ── Room availability ─────────────────────────────────────────────────────────

@reservation_bp.route("/availability", methods=["GET"])
def get_available_rooms():
    hotel_id = request.args.get("hotel_id", type=int)
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")

    if not all([hotel_id, start_str, end_str]):
        return jsonify({"error": "hotel_id, start_date, end_date required"}), 400

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Dates must be YYYY-MM-DD"}), 400

    if end_date <= start_date:
        return jsonify({"error": "end_date must be after start_date"}), 400

    available_ids = room_availability(start_date, end_date, hotel_id)

    with Session(engine) as db:
        rooms = db.execute(
            select(HotelRoom).where(HotelRoom.id.in_(available_ids))
        ).scalars().all()
        return jsonify([
            {"id": r.id, "room": r.room, "room_type": r.room_type.value}
            for r in rooms
        ]), 200


# ── List bookings ─────────────────────────────────────────────────────────────

@reservation_bp.route("/", methods=["GET"])
@jwt_required()
def list_bookings():
    user_id = int(get_jwt_identity())
    with Session(engine) as db:
        bookings = db.execute(
            select(Booking)
            .where(Booking.user == user_id)
            .order_by(Booking.created_at.desc())
        ).scalars().all()

        results = []
        for b in bookings:
            room = db.get(HotelRoom, b.room)
            hotel = db.get(Hotel, room.hotel) if room else None
            results.append({
                "id": b.id,
                "booking_number": b.booking_number,
                "title": b.title,
                "hotel_id": hotel.id if hotel else None,
                "hotel_name": hotel.name if hotel else None,
                "hotel_city": hotel.city if hotel else None,
                "room_type": room.room_type.value if room else None,
                "start_date": b.start_date.isoformat(),
                "end_date": b.end_date.isoformat(),
                "total_price": str(b.total_price),
                "status": b.status.value,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "refundable": b.refundable,
            })
        return jsonify(results), 200


# ── Create booking ────────────────────────────────────────────────────────────

@reservation_bp.route("/", methods=["POST"])
@jwt_required()
def create_booking():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    title = data.get("title")
    room_id = data.get("room")
    start_str = data.get("start_date")
    end_str = data.get("end_date")

    if not all([title, room_id, start_str, end_str]):
        return jsonify({"error": "title, room, start_date, end_date required"}), 400

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Dates must be YYYY-MM-DD"}), 400

    if end_date <= start_date:
        return jsonify({"error": "end_date must be after start_date"}), 400
    if start_date < date.today():
        return jsonify({"error": "start_date cannot be in the past"}), 400

    with Session(engine) as db:
        room = db.execute(
            select(HotelRoom).where(HotelRoom.id == room_id).with_for_update()
        ).scalar_one_or_none()
        if not room:
            return jsonify({"error": "Room not found"}), 404

        hotel = db.get(Hotel, room.hotel)
        if not hotel:
            return jsonify({"error": "Hotel not found"}), 404

        conflicts = check_room_availability(db, room_id, start_date, end_date)
        if conflicts:
            return jsonify({
                "error": "Room unavailable for selected dates",
                "conflicts": [
                    {
                        "booking_id": c.id,
                        "start_date": c.start_date.isoformat(),
                        "end_date": c.end_date.isoformat(),
                    }
                    for c in conflicts
                ],
            }), 409

        total = calculate_total_price(hotel.price_per_night, start_date, end_date)
        booking = Booking(
            booking_number=generate_booking_number(),
            title=title,
            user=user_id,
            room=room_id,
            start_date=start_date,
            end_date=end_date,
            total_price=total,
            status=Status.INPROGRESS,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=5),
        )
        db.add(booking)
        db.commit()

        return jsonify({
            "message": "Booking created — confirm within 5 minutes",
            "booking": {
                "id": booking.id,
                "booking_number": booking.booking_number,
                "title": booking.title,
                "hotel_name": hotel.name,
                "hotel_city": hotel.city,
                "start_date": booking.start_date.isoformat(),
                "end_date": booking.end_date.isoformat(),
                "total_price": str(booking.total_price),
                "status": booking.status.value,
                "expires_at": booking.expires_at.isoformat(),
                "refundable": booking.refundable,
            },
        }), 201


# ── Get single booking ────────────────────────────────────────────────────────

@reservation_bp.route("/<int:booking_id>", methods=["GET"])
@jwt_required()
def get_booking(booking_id):
    user_id = int(get_jwt_identity())
    with Session(engine) as db:
        booking = db.execute(
            select(Booking).where(and_(Booking.id == booking_id, Booking.user == user_id))
        ).scalar_one_or_none()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        room = db.get(HotelRoom, booking.room)
        hotel = db.get(Hotel, room.hotel) if room else None

        return jsonify({
            "id": booking.id,
            "booking_number": booking.booking_number,
            "title": booking.title,
            "hotel_id": hotel.id if hotel else None,
            "hotel_name": hotel.name if hotel else None,
            "hotel_city": hotel.city if hotel else None,
            "room_type": room.room_type.value if room else None,
            "start_date": booking.start_date.isoformat(),
            "end_date": booking.end_date.isoformat(),
            "total_price": str(booking.total_price),
            "status": booking.status.value,
            "expires_at": booking.expires_at.isoformat() if booking.expires_at else None,
            "refundable": booking.refundable,
        }), 200


def _validate_reschedule_input(data):
    title = data.get("title")
    room_id = data.get("room")
    start_str = data.get("start_date")
    end_str = data.get("end_date")

    if not all([title, room_id, start_str, end_str]):
        return None, jsonify({"error": "title, room, start_date, end_date required"}), 400

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except (ValueError, TypeError):
        return None, jsonify({"error": "Dates must be YYYY-MM-DD"}), 400

    if end_date <= start_date:
        return None, jsonify({"error": "end_date must be after start_date"}), 400
    if start_date < date.today():
        return None, jsonify({"error": "start_date cannot be in the past"}), 400

    return (title, room_id, start_date, end_date), None, None


@reservation_bp.route("/<int:booking_id>", methods=["PATCH"])
@jwt_required()
def reschedule_booking(booking_id): # pylint: disable=too-many-locals
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    parsed, error_response, error_code = _validate_reschedule_input(data)
    if error_response:
        return error_response, error_code

    title, room_id, start_date, end_date = parsed

    with Session(engine) as db:
        booking = db.execute(
            select(Booking).where(and_(Booking.id == booking_id, Booking.user == user_id))
        ).scalar_one_or_none()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking.status in (Status.CANCELLED, Status.COMPLETED):
            return jsonify({"error": "Booking cannot be rescheduled"}), 400

        room = db.execute(
            select(HotelRoom).where(HotelRoom.id == room_id).with_for_update()
        ).scalar_one_or_none()
        if not room:
            return jsonify({"error": "Room not found"}), 404

        hotel = db.get(Hotel, room.hotel)
        if not hotel:
            return jsonify({"error": "Hotel not found"}), 404

        conflicts = _reschedule_conflicts(
            db, room_id, booking.id, start_date, end_date
        )
        if conflicts:
            return jsonify({
                "error": "Room unavailable for selected dates",
                "conflicts": [
                    {
                        "booking_id": c.id,
                        "start_date": c.start_date.isoformat(),
                        "end_date": c.end_date.isoformat(),
                    }
                    for c in conflicts
                ],
            }), 409

        original_price = booking.total_price
        new_price = calculate_total_price(hotel.price_per_night, start_date, end_date)
        price_difference = new_price - original_price

        booking.title = title
        booking.room = room_id
        booking.start_date = start_date
        booking.end_date = end_date
        booking.total_price = new_price
        if booking.status == Status.INPROGRESS:
            booking.expires_at = datetime.now() + timedelta(minutes=5)

        db.commit()

        pricing_summary = _pricing_summary(price_difference)

        return jsonify({
            "message": "Booking updated",
            "booking": {
                "id": booking.id,
                "booking_number": booking.booking_number,
                "title": booking.title,
                "hotel_name": hotel.name,
                "hotel_city": hotel.city,
                "start_date": booking.start_date.isoformat(),
                "end_date": booking.end_date.isoformat(),
                "original_price": str(original_price),
                "total_price": str(booking.total_price),
                "status": booking.status.value,
                "expires_at": booking.expires_at.isoformat() if booking.expires_at else None,
                "refundable": booking.refundable,
            },
            "pricing_summary": pricing_summary,
        }), 200


# ── Confirm booking ──────────────────────────────────────────

@reservation_bp.route("/<int:booking_id>/confirm", methods=["POST"])
@jwt_required()
def confirm_booking(booking_id):
    user_id = int(get_jwt_identity())
    with Session(engine) as db:
        booking = db.execute(
            select(Booking).where(and_(Booking.id == booking_id, Booking.user == user_id))
        ).scalar_one_or_none()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking.status == Status.CANCELLED:
            return jsonify({"error": "Booking was cancelled"}), 400
        if booking.status in (Status.CONFIRMED, Status.COMPLETED):
            return jsonify({"error": "Already confirmed"}), 400
        if booking.expires_at and booking.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            booking.status = Status.CANCELLED
            db.commit()
            return jsonify({"error": "Booking expired — please start over"}), 400

        booking.status = Status.CONFIRMED
        booking.expires_at = None

        overlapping = db.execute(
            select(Booking).where(
                and_(
                    Booking.user == user_id,
                    Booking.id != booking_id,
                    Booking.status == Status.CONFIRMED,
                    Booking.start_date < booking.end_date,
                    Booking.end_date > booking.start_date
                )
            )
        ).scalars().all()

        for old in overlapping:
            old.refundable = False

        points_earned = 0
        if not overlapping:
            points_earned = int(float(booking.total_price) * POINTS_PER_DOLLAR)
            user = db.get(User, user_id)
            user.points += points_earned
            db.add(PointsTransaction(
                user_id = user_id,
                booking_id = booking_id,
                points = points_earned,
                log = f"Earned {points_earned} points on transaction {booking.booking_number}",
            ))

        db.commit()
        return jsonify({
            "message": "Booking confirmed",
            "booking_number": booking.booking_number,
            "points_earned": points_earned, 
        }), 200


# ── Cancel booking ────────────────────────────────────────────────────────────

@reservation_bp.route("/<int:booking_id>/cancellation-preview", methods=["GET"])
@jwt_required()
def get_cancellation_preview(booking_id):
    user_id = int(get_jwt_identity())
    with Session(engine) as db:
        booking = db.execute(
            select(Booking).where(and_(Booking.id == booking_id, Booking.user == user_id))
        ).scalar_one_or_none()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking.status == Status.CANCELLED:
            return jsonify({"error": "Booking is already cancelled"}), 400
        if booking.status == Status.COMPLETED:
            return jsonify({"error": "Completed bookings cannot be cancelled"}), 400

        restored_points = abs(
            db.execute(
                select(func.sum(PointsTransaction.points)).where(
                    and_(
                        PointsTransaction.booking_id == booking_id,
                        PointsTransaction.points < 0,
                    )
                )
            ).scalar()
            or 0
        )
        details = get_cancellation_details(db, booking)
        if not details["allowed"]:
            return jsonify({
                "error": "Reservations can only be cancelled at least 48 hours before check-in",
                "cancellation": _cancellation_payload(booking, details, restored_points),
            }), 400

        return jsonify({
            "message": "Review cancellation details before confirming",
            "cancellation": _cancellation_payload(booking, details, restored_points),
        }), 200

@reservation_bp.route("/<int:booking_id>", methods=["DELETE"])
@jwt_required()
def cancel_booking(booking_id):
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    confirmed = bool(data.get("confirmed"))
    with Session(engine) as db:
        booking = db.execute(
            select(Booking).where(and_(Booking.id == booking_id, Booking.user == user_id))
        ).scalar_one_or_none()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking.status == Status.CANCELLED:
            return jsonify({"error": "Already cancelled"}), 400
        if booking.status == Status.COMPLETED:
            return jsonify({"error": "Completed bookings cannot be cancelled"}), 400

        redeemed_points = abs(
            db.execute(
                select(func.sum(PointsTransaction.points)).where(
                    and_(
                        PointsTransaction.booking_id == booking_id,
                        PointsTransaction.points < 0,
                    )
                )
            ).scalar()
            or 0
        )
        details = get_cancellation_details(db, booking)
        if not details["allowed"]:
            return jsonify({
                "error": "Reservations can only be cancelled at least 48 hours before check-in",
                "cancellation": _cancellation_payload(booking, details, redeemed_points),
            }), 400

        if not confirmed:
            return jsonify({
                "message": "Confirm cancellation to process the refund",
                "requires_confirmation": True,
                "cancellation": _cancellation_payload(booking, details, redeemed_points),
            }), 200

        # Reverse any points earned when this booking was confirmed
        earned = db.execute(
            select(func.sum(PointsTransaction.points)).where(
                and_(
                    PointsTransaction.booking_id == booking_id,
                    PointsTransaction.points > 0,
                )
            )
        ).scalar() or 0

        if earned > 0:
            user = db.get(User, user_id)
            if user:
                user.points = max(0, user.points - earned)
                db.add(PointsTransaction(
                    user_id=user_id,
                    booking_id=booking_id,
                    points=-earned,
                    log=f"Reversed {earned} earned points for cancelled booking {booking.booking_number}",
                ))

        if redeemed_points > 0 and booking.refundable:
            user = db.get(User, user_id)
            if user:
                user.points += redeemed_points
                db.add(PointsTransaction(
                    user_id=user_id,
                    booking_id=booking_id,
                    points=redeemed_points,
                    log=f"Restored {redeemed_points} redeemed points for cancelled booking {booking.booking_number}",
                ))

        booking.status = Status.CANCELLED
        try:
            db.commit()
        except (IntegrityError, SQLAlchemyError):
            db.rollback()
            return jsonify({
                "error": "Cancellation failed. Please try again.",
            }), 500

        user = db.get(User, user_id)
        email_sent = False
        if user and user.email:
            email_sent = send_cancellation_email(
                to_email=user.email,
                booking_number=booking.booking_number,
                fee_amount=details["fee_amount"],
                refund_amount=details["refund_amount"],
            )

        return jsonify({
            "message": "Booking cancelled",
            "booking_number": booking.booking_number,
            "refund": {
                "processed": True,
                "amount": str(details["refund_amount"]),
                "fee_amount": str(details["fee_amount"]),
                "points_restored": int(redeemed_points),
            },
            "email_sent": email_sent,
        }), 200


@reservation_bp.route("/<int:booking_id>/email-receipt", methods=["POST"])
@jwt_required()
def email_receipt(booking_id):
    user_id = int(get_jwt_identity())
    with Session(engine) as db:
        booking = db.execute(
            select(Booking).where(and_(Booking.id == booking_id, Booking.user == user_id))
        ).scalar_one_or_none()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        user = db.get(User, user_id)
        if not user or not user.email:
            return jsonify({"error": "No email address on file for this account"}), 400

        room  = db.get(HotelRoom, booking.room)
        hotel = db.get(Hotel, room.hotel) if room else None

        n = (booking.end_date - booking.start_date).days
        total = float(booking.total_price)
        fee   = round(total * 0.10, 2)

        receipt_rows = [
            ("Booking Number", booking.booking_number),
            ("Trip Title",     booking.title),
            ("Hotel",          hotel.name  if hotel else "—"),
            ("City",           hotel.city  if hotel else "—"),
            ("Room Type",      room.room_type.value.capitalize() if room else "—"),
            ("Check-in",       booking.start_date.isoformat()),
            ("Check-out",      booking.end_date.isoformat()),
            ("Nights",         str(n)),
            ("Status",         booking.status.value.capitalize()),
            ("Total Price",    f"${total:.2f}"),
            ("Cancellation Fee (10%)", f"${fee:.2f}"),
        ]

        table_rows = "".join(
            f"<tr><td class='label'>{k}</td><td class='value'>{v}</td></tr>"
            for k, v in receipt_rows
        )

        issued_on = datetime.now().strftime("%B %d, %Y")
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
      padding: 40px 16px;
      color: #1a1a2e;
    }}
    .card {{
      background: #fff;
      max-width: 600px;
      margin: 0 auto;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0,0,0,.08);
    }}
    .card-header {{
      background: #1a1a2e;
      padding: 28px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .brand {{
      font-size: 20px;
      font-weight: 900;
      color: #a78bfa;
      letter-spacing: -0.5px;
    }}
    .receipt-label {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #9ca3af;
      text-align: right;
    }}
    .receipt-label strong {{
      display: block;
      font-size: 16px;
      color: #fff;
      text-transform: none;
      letter-spacing: 0;
      margin-top: 2px;
    }}
    .card-body {{ padding: 28px 32px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    tr:nth-child(even) td {{ background: #f9fafb; }}
    td {{ padding: 10px 14px; font-size: 14px; }}
    td.label {{ font-weight: 600; color: #6b7280; width: 46%; }}
    td.value {{ color: #111827; }}
    .footer {{
      padding: 20px 32px;
      border-top: 1px solid #e5e7eb;
      font-size: 12px;
      color: #9ca3af;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="card-header">
      <div class="brand">LuxuryHotels</div>
      <div class="receipt-label">
        Booking Receipt
        <strong>{booking.booking_number}</strong>
      </div>
    </div>
    <div class="card-body">
      <table><tbody>{table_rows}</tbody></table>
    </div>
    <div class="footer">
      Issued on {issued_on} &nbsp;·&nbsp; Thank you for staying with us.
    </div>
  </div>
</body>
</html>"""

        try:
            sent = send_receipt_email(
                to_email=user.email,
                booking_number=booking.booking_number,
                html_body=html_body,
            )
        except Exception:  # pylint: disable=broad-except
            return jsonify({"error": "Failed to send receipt email. Please try again."}), 500

        if not sent:
            return jsonify({"error": "Failed to send receipt email. Please try again."}), 500

        return jsonify({
            "message": "Receipt sent",
            "booking_number": booking.booking_number,
            "sent_to": user.email,
        }), 200