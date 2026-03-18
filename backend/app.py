import os
from flask import Flask
from flask_smorest import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret"),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "jwt-dev-secret"),
        API_TITLE="LikeHome API",
        API_VERSION="v1",
        OPENAPI_VERSION="3.0.3",
        OPENAPI_URL_PREFIX="/",
        OPENAPI_SWAGGER_UI_PATH="/api/docs",
        OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    )

    CORS(app)
    JWTManager(app)

    api = Api(app)

    from api_docs import auth_bp, hotels_bp, bookings_bp, payments_bp, rewards_bp

    api.register_blueprint(auth_bp, url_prefix="/api/auth")
    api.register_blueprint(hotels_bp, url_prefix="/api/hotels")
    api.register_blueprint(bookings_bp, url_prefix="/api/bookings")
    api.register_blueprint(payments_bp, url_prefix="/api/payments")
    api.register_blueprint(rewards_bp, url_prefix="/api/rewards")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
