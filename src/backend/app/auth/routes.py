#registration endpoint
from flask import app, request, jsonify
from . import auth_bp
from backend.models.models import User
from backend.database.db_connection import session
from backend.app.extensions import bcrypt
from sqlalchemy.exc import IntegrityError

@auth_bp.route("/register", methods=["POST"])
def register():
    #read data
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    #required fields validation for bad request
    if not email or not password:
        return jsonify({"message": "email and password are required"}), 400
    
    #hash password
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    #create user
    new_user = User(
    email=email,
    password=hashed_password)

    #save to db with error handling for duplicate email
    try:
        session.add(new_user)
        session.commit()
    except IntegrityError:
        session.rollback()
        return jsonify({"message": "email already exists"}), 409
  

    #return response
    return jsonify({"message": "user registered successfully"}), 201