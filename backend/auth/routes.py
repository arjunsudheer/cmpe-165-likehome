# registration endpoint
from flask import current_app, request, jsonify
from sqlalchemy.exc import IntegrityError
from backend.auth import auth_bp
from backend.auth.forms import validate_login, validate_registration
from backend.db.models import User
from backend.db.db_connection import session
from backend.auth.password_utils import bcrypt
from google.oauth2 import id_token
from google.auth.transport import requests as grequests


# registration endpoint US-A01.2, US-A01.3
@auth_bp.route("/register", methods=["POST"])
def register():
    # read data
    data = request.get_json(silent=True)
    # check for valid data
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    # validate data
    validation_error = validate_registration(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400
    email = data.get("email")
    password = data.get("password")
    # hash password
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    # create user
    new_user = User(email=email.lower(), password=hashed_password)
    # save to db with error handling for duplicate email
    try:
        session.add(new_user)
        session.commit()
    except IntegrityError:
        session.rollback()
        return jsonify({"message": "email already exists"}), 409
    # return response
    return jsonify({"message": "user registered successfully"}), 201


# oauth login endpoint US-A01.4
@auth_bp.route("/oauth-login", methods=["POST"])
def oauth_login():
    data = request.get_json()

    # check for valid data
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    token = data.get("token")

    # check for token
    if not token:
        return jsonify({"error": "Token is required"}), 400
    try:
        # Verify the token and get user info
        id_info = id_token.verify_oauth2_token(
            token, grequests.Request(), current_app.config["GOOGLE_CLIENT_ID"]
        )
        email = id_info.get("email")
        if not email:
            return jsonify({"error": "Email not found in token"}), 400
        # Check if user exists, if not create a new user
        user = session.query(User).filter_by(email=email).first()
        if not user:
            user = User(email=email, password=None)
            session.add(user)
            session.commit()
        return jsonify({"message": "Google login successful", "email": email}), 200
    except ValueError:
        return jsonify({"error": "Invalid token"}), 400


# login endpoint US-A02.1
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    # check for valid data
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    # validate data
    validation_error = validate_login(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400
    email = data.get("email")
    password = data.get("password")
    user = session.query(User).filter_by(email=email).first()
    # check if user exists and password is correct
    if user and bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Login successful", "email": email}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401
