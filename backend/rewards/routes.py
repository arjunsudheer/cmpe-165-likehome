from decimal import Decimal

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.db_connection import engine
from backend.db.models import Booking, PointsTransaction, Status, User
from backend.rewards import rewards_bp


@rewards_bp.route("/balance", methods=["GET"])
@jwt_required()
def get_balance():
    user_id = int(get_jwt_identity())
    with Session(engine) as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "user_id": user_id,
            "total_points": user.points,
            "dollar_value": round(user.points / 100, 2),
        }), 200


@rewards_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    with Session(engine) as db:
        txs = db.execute(
            select(PointsTransaction)
            .where(PointsTransaction.user_id == user_id)
            .order_by(PointsTransaction.recorded_at.desc())
        ).scalars().all()
        return jsonify([
            {
                "id": tx.id,
                "booking_id": tx.booking_id,
                "points": tx.points,
                "recorded_at": tx.recorded_at.isoformat() if tx.recorded_at else None,
            }
            for tx in txs
        ]), 200


@rewards_bp.route("/redeem", methods=["POST"])
@jwt_required()
def redeem_points():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    points = data.get("points", 0)
    booking_id = data.get("booking_id")

    if not isinstance(points, int) or points <= 0:
        return jsonify({"error": "points must be a positive integer"}), 400
    if not booking_id:
        return jsonify({"error": "booking_id is required"}), 400

    with Session(engine) as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        booking = db.get(Booking, booking_id)
        if not booking or booking.user != user_id:
            return jsonify({"error": "Booking not found"}), 404
        if booking.status != Status.INPROGRESS:
            return jsonify({
                "error": "Rewards can only be applied at checkout before the booking is confirmed",
            }), 400
        if points > user.points:
            return jsonify({"error": f"Only {user.points} pts available"}), 400

        # 100 pts = $1; cap at booking total
        max_pts = int(float(booking.total_price) * 100)
        if points > max_pts:
            return jsonify({"error": f"Max redeemable is {max_pts} pts"}), 400

        discount = Decimal(points) / Decimal(100)
        booking.total_price = max(Decimal("0.00"), booking.total_price - discount)
        user.points -= points
        db.add(PointsTransaction(user_id=user_id, booking_id=booking_id, points=-points, log=f"Redeemed {points} points on booking #{booking_id}"))
        db.commit()

        return jsonify({
            "message": "Points redeemed",
            "points_used": points,
            "new_total": str(booking.total_price),
            "remaining_points": user.points,
        }), 200
