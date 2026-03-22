# registration endpoint
from flask import current_app, jsonify, request
from google.auth.transport import requests as grequests
from google.oauth2 import id_token
from sqlalchemy.exc import IntegrityError

from backend.auth import auth_bp
from backend.auth.forms import validate_login, validate_registration
from backend.db.db_connection import session
from backend.db.models import User
from backend import bcrypt


# registration endpoint US-A01.2, US-A01.3
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    validation_error = validate_registration(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    email = data.get("email")
    password = data.get("password")
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(email=email.lower(), password=hashed_password)

    try:
        session.add(new_user)
        session.commit()
    except IntegrityError:
        session.rollback()
        return jsonify({"message": "email already exists"}), 409

    return jsonify({"message": "user registered successfully"}), 201


# oauth login endpoint US-A01.4
@auth_bp.route("/oauth-login", methods=["POST"])
def oauth_login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    token = data.get("token")
    if not token:
        return jsonify({"error": "Token is required"}), 400

    try:
        id_info = id_token.verify_oauth2_token(
            token, grequests.Request(), current_app.config["GOOGLE_CLIENT_ID"]
        )
        email = id_info.get("email")
        if not email:
            return jsonify({"error": "Email not found in token"}), 400

        user = session.query(User).filter_by(email=email).first()
        if not user:
            placeholder_password = bcrypt.generate_password_hash(
                f"oauth:{email.lower()}"
            ).decode("utf-8")
            user = User(email=email.lower(), password=placeholder_password)
            session.add(user)
            session.commit()

        return jsonify({"message": "Google login successful", "email": email}), 200
    except ValueError:
        return jsonify({"error": "Invalid token"}), 400


# login endpoint US-A02.1
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    validation_error = validate_login(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    email = data.get("email")
    password = data.get("password")
    user = session.query(User).filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Login successful", "email": email}), 200

    return jsonify({"error": "Invalid email or password"}), 401
