#create auth blueprint 

from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

# import routes after blueprint is created to avoid circular imports
from app.auth import routes




