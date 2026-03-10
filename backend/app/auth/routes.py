#registration endpoint
from flask import request, jsonify
from . import auth_bp
from backend.models.models import User
from backend.database.db_connection import session
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

@auth_bp.route("/register", methods=["POST"])
def register():
    #read data
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    #hash password
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    #create user
    new_user = User(
    email=email,
    password=hashed_password)

    #save to db
    session.add(new_user)
    session.commit()

    #return response
    return jsonify({"message": "user registered successfully"}), 201