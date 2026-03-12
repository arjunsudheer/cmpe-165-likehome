#registration endpoint
from flask import request, jsonify
from sqlalchemy.exc import IntegrityError

from backend.app.auth import auth_bp
from backend.app.auth.forms import validate_registration 

from backend.models.models import User
from backend.database.db_connection import session
from backend.app.extensions import bcrypt

@auth_bp.route("/register", methods=["POST"])
def register():
    #read data
    data = request.get_json()
    #email format and password match validation
    validation_error = validate_registration(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400
    email = data.get("email")
    password = data.get("password")


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