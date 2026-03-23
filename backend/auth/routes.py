from flask import jsonify, request
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

from backend.auth import auth_bp
from backend.auth.forms import validate_login, validate_registration
from backend.db.db_connection import session
from backend.db.models import User
from backend.extensions import bcrypt


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    err = validate_registration(data)
    if err:
        return jsonify({"error": err}), 400

    name = (data.get("name") or "").strip() or None
    email = data.get("email").lower()
    hashed = bcrypt.generate_password_hash(data.get("password")).decode("utf-8")
    user = User(name=name, email=email, password=hashed)

    try:
        session.add(user)
        session.commit()
    except IntegrityError:
        session.rollback()
        # Signal to frontend: redirect user to login instead
        return jsonify({"error": "email_exists"}), 409

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    err = validate_login(data)
    if err:
        return jsonify({"error": err}), 400

    email = data.get("email").lower()
    user = session.query(User).filter_by(email=email).first()

    if user is None:
        # Signal to frontend: redirect user to register instead
        return jsonify({"error": "email_not_found"}), 404

    if not bcrypt.check_password_hash(user.password, data.get("password")):
        return jsonify({"error": "Incorrect password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
    }), 200
