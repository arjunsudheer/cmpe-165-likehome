from flask import current_app, jsonify, request
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

from backend.auth import auth_bp
from backend.auth.forms import validate_login, validate_registration
from backend.db.db_connection import session
from backend.db.models import User
from backend.extensions import bcrypt


def _token_response(user):
    """Build the standard auth response dict for any login/register flow."""
    token = create_access_token(identity=str(user.id))
    return {
        "access_token": token,
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
    }


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
        # 409 tells the frontend to redirect to login instead
        return jsonify({"error": "email_exists"}), 409

    return jsonify(_token_response(user)), 201


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
        # 404 tells the frontend to redirect to register instead
        return jsonify({"error": "email_not_found"}), 404

    if not bcrypt.check_password_hash(user.password, data.get("password")):
        return jsonify({"error": "Incorrect password"}), 401

    return jsonify(_token_response(user)), 200


@auth_bp.route("/google", methods=["POST"])
def google_login():
    """Verify a Google ID token and return a JWT. Creates the user if new."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    credential = data.get("credential")
    if not credential:
        return jsonify({"error": "credential is required"}), 400

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        return jsonify({"error": "Google OAuth is not configured on this server"}), 501

    try:
        from google.auth.transport import requests as grequests
        from google.oauth2 import id_token as google_id_token

        id_info = google_id_token.verify_oauth2_token(
            credential, grequests.Request(), client_id
        )
    except ValueError as exc:
        return jsonify({"error": f"Invalid Google token: {exc}"}), 400

    email = (id_info.get("email") or "").lower()
    if not email:
        return jsonify({"error": "Google account has no email"}), 400

    user = session.query(User).filter_by(email=email).first()
    if not user:
        # Auto-create account on first Google sign-in
        placeholder = bcrypt.generate_password_hash(f"google:{email}").decode("utf-8")
        user = User(
            name=id_info.get("name"),
            email=email,
            password=placeholder,
        )
        session.add(user)
        session.commit()

    return jsonify(_token_response(user)), 200
