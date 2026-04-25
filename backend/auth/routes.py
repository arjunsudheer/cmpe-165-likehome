import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from flask import current_app, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from backend.auth import auth_bp
from backend.auth.forms import (
    validate_email,
    validate_login,
    validate_password,
    validate_registration,
)
from backend.auth.password_utils import hash_password
from backend.db.db_connection import session
from backend.db.models import Notification, PasswordResetToken, User
from backend.extensions import bcrypt
from backend.utils.email import send_email


def _token_response(user):
    """Build the standard auth response dict for any login/register flow."""
    token = create_access_token(identity=str(user.id))
    return {
        "access_token": token,
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "send_reminder_email": user.send_reminder_email,
    }


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _hash_reset_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _password_reset_message():
    return (
        "If an account exists for that email, we have sent password reset instructions."
    )


def _build_reset_link(token):
    base = current_app.config.get("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    return f"{base}/reset-password?token={token}"


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
    hashed = hash_password(data.get("password"))
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


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    err = validate_email(email)
    if err:
        return jsonify({"error": err}), 400

    user = session.query(User).filter_by(email=email).first()
    if user:
        ttl_seconds = current_app.config.get("PASSWORD_RESET_TOKEN_TTL_SECONDS", 3600)
        now = _utcnow()
        token = secrets.token_urlsafe(32)
        token_hash = _hash_reset_token(token)
        expires_at = now + timedelta(seconds=ttl_seconds)

        session.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).update({"used_at": now}, synchronize_session=False)
        session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        session.commit()

        reset_link = _build_reset_link(token)
        email_sent = send_email(
            user.email,
            "LikeHome password reset",
            "\n".join(
                [
                    "We received a request to reset your LikeHome password.",
                    "",
                    "Open the link below to choose a new password:",
                    reset_link,
                    "",
                    "This link expires in 1 hour.",
                    "If you did not request this, you can safely ignore this email.",
                ]
            ),
        )

        payload = {"message": _password_reset_message()}
        if current_app.testing or current_app.config.get("EXPOSE_RESET_TOKEN_IN_RESPONSE", False):
            payload["reset_token"] = token
            payload["reset_url"] = reset_link
            payload["email_sent"] = bool(email_sent)
        return jsonify(payload), 200

    return jsonify({"message": _password_reset_message()}), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    password = data.get("password")

    if not token:
        return jsonify({"error": "token is required"}), 400

    err = validate_password(password)
    if err:
        return jsonify({"error": err}), 400

    now = _utcnow()
    token_hash = _hash_reset_token(token)
    reset_record = session.query(PasswordResetToken).filter_by(
        token_hash=token_hash
    ).first()

    if (
        reset_record is None
        or reset_record.used_at is not None
        or reset_record.expires_at < now
    ):
        return jsonify({"error": "This reset link is invalid or has expired"}), 400

    user = session.query(User).filter_by(id=reset_record.user_id).first()
    if user is None:
        return jsonify({"error": "This reset link is invalid or has expired"}), 400

    user.password = hash_password(password)
    reset_record.used_at = now
    session.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.id != reset_record.id,
    ).update({"used_at": now}, synchronize_session=False)
    session.commit()

    return jsonify({"message": "Password updated successfully"}), 200

@auth_bp.route("/settings", methods=["GET"])
@jwt_required()
def get_settings():
    user_id = get_jwt_identity()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "send_reminder_email": user.send_reminder_email
    }), 200

@auth_bp.route("/settings", methods=["PUT"])
@jwt_required()
def update_settings():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if "send_reminder_email" in data:
        user.send_reminder_email = bool(data["send_reminder_email"])
        session.commit()

    return jsonify({
        "send_reminder_email": user.send_reminder_email
    }), 200


@auth_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    notifications = session.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    return jsonify([{
        "id": n.id,
        "message": n.message,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat()
    } for n in notifications]), 200

@auth_bp.route("/notifications/<int:notification_id>/mark-read", methods=["POST"])
@jwt_required()
def mark_notification_read(notification_id):
    user_id = get_jwt_identity()
    notification = session.query(Notification).filter_by(id=notification_id, user_id=user_id).first()
    
    if not notification:
        return jsonify({"error": "Notification not found"}), 404
        
    notification.is_read = True
    session.commit()
    
    return jsonify({"success": True}), 200

@auth_bp.route("/notifications/mark-all-read", methods=["POST"])
@jwt_required()
def mark_all_notifications_read():
    user_id = get_jwt_identity()
    session.query(Notification).filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    session.commit()
    
    return jsonify({"success": True}), 200
