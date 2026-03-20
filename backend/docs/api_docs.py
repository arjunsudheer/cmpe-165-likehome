import marshmallow as ma
from flask.views import MethodView
from flask_smorest import Blueprint

# ---------------------------------------------------------------------------
# Blueprints
# ---------------------------------------------------------------------------
auth_bp = Blueprint("auth", __name__, description="Authentication endpoints")
hotels_bp = Blueprint("hotels", __name__, description="Hotel search and details")
bookings_bp = Blueprint("bookings", __name__, description="Booking management")
payments_bp = Blueprint("payments", __name__, description="Payment processing")
rewards_bp = Blueprint("rewards", __name__, description="Rewards and loyalty points")

# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class RegisterRequestSchema(ma.Schema):
    email = ma.fields.Email(required=True, metadata={"example": "guest@example.com"})
    password = ma.fields.String(required=True, load_only=True, metadata={"example": "SecureP@ss1"})
    confirm_password = ma.fields.String(required=True, load_only=True, metadata={"example": "SecureP@ss1"})


class LoginRequestSchema(ma.Schema):
    email = ma.fields.Email(required=True, metadata={"example": "guest@example.com"})
    password = ma.fields.String(required=True, load_only=True, metadata={"example": "SecureP@ss1"})


class TokenResponseSchema(ma.Schema):
    access_token = ma.fields.String(metadata={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."})
    token_type = ma.fields.String(metadata={"example": "bearer"})


class MessageResponseSchema(ma.Schema):
    message = ma.fields.String(metadata={"example": "Operation successful"})


class ErrorResponseSchema(ma.Schema):
    error = ma.fields.String(metadata={"example": "Invalid email or password"})


class GoogleLoginRequestSchema(ma.Schema):
    token = ma.fields.String(required=True, metadata={"example": "google-oauth2-id-token..."})


# ---------------------------------------------------------------------------
# Hotel schemas
# ---------------------------------------------------------------------------

class HotelSchema(ma.Schema):
    id = ma.fields.Integer(dump_only=True, metadata={"example": 1})
    name = ma.fields.String(required=True, metadata={"example": "Grand Palace Hotel"})
    price_per_night = ma.fields.Decimal(required=True, as_string=True, metadata={"example": "149.99"})
    city = ma.fields.String(required=True, metadata={"example": "San Jose"})
    address = ma.fields.String(required=True, metadata={"example": "123 Main St"})
    rating = ma.fields.Decimal(as_string=True, metadata={"example": "4.5"})


class HotelQuerySchema(ma.Schema):
    city = ma.fields.String(metadata={"example": "San Jose"})
    min_price = ma.fields.Decimal(as_string=True, metadata={"example": "50.00"})
    max_price = ma.fields.Decimal(as_string=True, metadata={"example": "300.00"})


class HotelRoomSchema(ma.Schema):
    id = ma.fields.Integer(dump_only=True, metadata={"example": 1})
    hotel = ma.fields.Integer(required=True, metadata={"example": 1})
    room = ma.fields.Integer(required=True, metadata={"example": 101})
    room_type = ma.fields.String(required=True, metadata={"example": "DOUBLE"})


# ---------------------------------------------------------------------------
# Booking schemas
# ---------------------------------------------------------------------------

class BookingRequestSchema(ma.Schema):
    title = ma.fields.String(required=True, metadata={"example": "Weekend getaway"})
    room = ma.fields.Integer(required=True, metadata={"example": 1})
    start_date = ma.fields.Date(required=True, metadata={"example": "2026-04-01"})
    end_date = ma.fields.Date(required=True, metadata={"example": "2026-04-03"})


class BookingResponseSchema(ma.Schema):
    id = ma.fields.Integer(dump_only=True, metadata={"example": 1})
    title = ma.fields.String(metadata={"example": "Weekend getaway"})
    user = ma.fields.Integer(metadata={"example": 1})
    room = ma.fields.Integer(metadata={"example": 1})
    start_date = ma.fields.Date(metadata={"example": "2026-04-01"})
    end_date = ma.fields.Date(metadata={"example": "2026-04-03"})
    total_price = ma.fields.Decimal(as_string=True, metadata={"example": "299.98"})
    status = ma.fields.String(metadata={"example": "CONFIRMED"})
    created_at = ma.fields.DateTime(dump_only=True)


# ---------------------------------------------------------------------------
# Review schemas
# ---------------------------------------------------------------------------

class ReviewRequestSchema(ma.Schema):
    hotel = ma.fields.Integer(required=True, metadata={"example": 1})
    title = ma.fields.String(metadata={"example": "Great stay!"})
    content = ma.fields.String(metadata={"example": "Clean rooms and friendly staff."})
    rating = ma.fields.Integer(required=True, metadata={"example": 5})


class ReviewResponseSchema(ma.Schema):
    id = ma.fields.Integer(dump_only=True, metadata={"example": 1})
    user = ma.fields.Integer(metadata={"example": 1})
    hotel = ma.fields.Integer(metadata={"example": 1})
    title = ma.fields.String(metadata={"example": "Great stay!"})
    content = ma.fields.String(metadata={"example": "Clean rooms and friendly staff."})
    rating = ma.fields.Integer(metadata={"example": 5})


# ---------------------------------------------------------------------------
# Payment schemas
# ---------------------------------------------------------------------------

class PaymentRequestSchema(ma.Schema):
    booking_id = ma.fields.Integer(required=True, metadata={"example": 1})
    amount = ma.fields.Decimal(required=True, as_string=True, metadata={"example": "299.98"})
    use_points = ma.fields.Integer(load_default=0, metadata={"example": 500})


class PaymentResponseSchema(ma.Schema):
    message = ma.fields.String(metadata={"example": "Payment processed"})
    amount_charged = ma.fields.Decimal(as_string=True, metadata={"example": "294.98"})
    points_used = ma.fields.Integer(metadata={"example": 500})


# ---------------------------------------------------------------------------
# Rewards schemas
# ---------------------------------------------------------------------------

class RewardBalanceSchema(ma.Schema):
    user_id = ma.fields.Integer(metadata={"example": 1})
    total_points = ma.fields.Integer(metadata={"example": 1500})
    dollar_value = ma.fields.Decimal(as_string=True, metadata={"example": "15.00"})


class PointsTransactionSchema(ma.Schema):
    id = ma.fields.Integer(dump_only=True, metadata={"example": 1})
    user_id = ma.fields.Integer(metadata={"example": 1})
    booking_id = ma.fields.Integer(metadata={"example": 1})
    points = ma.fields.Integer(metadata={"example": 150})
    recorded_at = ma.fields.DateTime(dump_only=True)


# ===========================================================================
# Auth endpoints
# ===========================================================================

@auth_bp.route("/register")
class Register(MethodView):
    @auth_bp.arguments(RegisterRequestSchema)
    @auth_bp.response(201, MessageResponseSchema)
    @auth_bp.alt_response(400, schema=ErrorResponseSchema, description="Validation error")
    @auth_bp.alt_response(409, schema=ErrorResponseSchema, description="Email already exists")
    def post(self, payload):
        """Register a new user.

        Creates a new user account. Password is hashed with bcrypt before storage.
        """
        return {"message": "Not implemented"}, 501

@auth_bp.route("/login")
class Login(MethodView):
    @auth_bp.arguments(LoginRequestSchema)
    @auth_bp.response(200, TokenResponseSchema)
    @auth_bp.alt_response(401, schema=ErrorResponseSchema, description="Invalid credentials")
    def post(self, payload):
        """Log in and receive a JWT access token.

        Returns a bearer token. Include it in subsequent requests as:
        `Authorization: Bearer <access_token>`
        """
        return {"message": "Not implemented"}, 501

@auth_bp.route("/google-login")
class GoogleLogin(MethodView):
    @auth_bp.arguments(GoogleLoginRequestSchema)
    @auth_bp.response(200, TokenResponseSchema)
    @auth_bp.alt_response(400, schema=ErrorResponseSchema, description="Invalid Google token")
    def post(self, payload):
        """Log in with a Google OAuth2 ID token.

        Verifies the Google token and returns a JWT. Creates the user account
        if it does not already exist.
        """
        return {"message": "Not implemented"}, 501


# ===========================================================================
# Hotels endpoints
# ===========================================================================

@hotels_bp.route("/")
class HotelList(MethodView):
    @hotels_bp.arguments(HotelQuerySchema, location="query")
    @hotels_bp.response(200, HotelSchema(many=True))
    def get(self, args):
        """Search hotels.

        Filter by city, min_price, and max_price. Returns all hotels if no
        filters are provided.
        """
        return []

@hotels_bp.route("/<int:hotel_id>")
class HotelDetail(MethodView):
    @hotels_bp.response(200, HotelSchema)
    @hotels_bp.alt_response(404, schema=ErrorResponseSchema, description="Hotel not found")
    def get(self, hotel_id):
        """Get hotel details by ID."""
        return {"message": "Not implemented"}, 501

@hotels_bp.route("/<int:hotel_id>/rooms")
class HotelRooms(MethodView):
    @hotels_bp.response(200, HotelRoomSchema(many=True))
    @hotels_bp.alt_response(404, schema=ErrorResponseSchema, description="Hotel not found")
    def get(self, hotel_id):
        """List available rooms for a hotel."""
        return []

@hotels_bp.route("/<int:hotel_id>/reviews")
class HotelReviews(MethodView):
    @hotels_bp.response(200, ReviewResponseSchema(many=True))
    def get(self, hotel_id):
        """List reviews for a hotel."""
        return []


# ===========================================================================
# Bookings endpoints (JWT required)
# ===========================================================================

@bookings_bp.route("/")
class BookingList(MethodView):
    @bookings_bp.response(200, BookingResponseSchema(many=True))
    @bookings_bp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """List bookings for the authenticated user.

        **Requires JWT.** Pass `Authorization: Bearer <token>` header.
        """
        return []

    @bookings_bp.arguments(BookingRequestSchema)
    @bookings_bp.response(201, BookingResponseSchema)
    @bookings_bp.alt_response(400, schema=ErrorResponseSchema, description="Validation error")
    @bookings_bp.doc(security=[{"bearerAuth": []}])
    def post(self, payload):
        """Create a new booking.

        **Requires JWT.** The user is inferred from the token.
        Total price is calculated from room rate and date range.
        """
        return {"message": "Not implemented"}, 501

@bookings_bp.route("/<int:booking_id>")
class BookingDetail(MethodView):
    @bookings_bp.response(200, BookingResponseSchema)
    @bookings_bp.alt_response(404, schema=ErrorResponseSchema, description="Booking not found")
    @bookings_bp.doc(security=[{"bearerAuth": []}])
    def get(self, booking_id):
        """Get booking details.

        **Requires JWT.** Users can only view their own bookings.
        """
        return {"message": "Not implemented"}, 501

    @bookings_bp.response(200, MessageResponseSchema)
    @bookings_bp.alt_response(404, schema=ErrorResponseSchema, description="Booking not found")
    @bookings_bp.doc(security=[{"bearerAuth": []}])
    def delete(self, booking_id):
        """Cancel a booking.

        **Requires JWT.** Sets the booking status to CANCELLED.
        """
        return {"message": "Not implemented"}, 501


# ===========================================================================
# Payments endpoints (JWT required)
# ===========================================================================

@payments_bp.route("/")
class ProcessPayment(MethodView):
    @payments_bp.arguments(PaymentRequestSchema)
    @payments_bp.response(200, PaymentResponseSchema)
    @payments_bp.alt_response(400, schema=ErrorResponseSchema, description="Validation error")
    @payments_bp.doc(security=[{"bearerAuth": []}])
    def post(self, payload):
        """Process a payment for a booking.

        **Requires JWT.** Optionally redeem reward points to reduce the amount.
        Points are converted at 100 points = $1.00.
        """
        return {"message": "Not implemented"}, 501


# ===========================================================================
# Rewards endpoints (JWT required)
# ===========================================================================

@rewards_bp.route("/balance")
class RewardBalance(MethodView):
    @rewards_bp.response(200, RewardBalanceSchema)
    @rewards_bp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """Get reward points balance for the authenticated user.

        **Requires JWT.** Returns total points and dollar equivalent
        (100 points = $1.00).
        """
        return {"message": "Not implemented"}, 501

@rewards_bp.route("/history")
class RewardHistory(MethodView):
    @rewards_bp.response(200, PointsTransactionSchema(many=True))
    @rewards_bp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """Get reward points transaction history.

        **Requires JWT.** Lists all point earnings and redemptions.
        """
        return []
