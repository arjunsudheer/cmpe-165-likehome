import re

EMAIL_REGEX = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"


def validate_email(email):
    if not email:
        return "Email is required"
    if not re.match(EMAIL_REGEX, email):
        return "Invalid email format"
    return None


def validate_password(password):
    if not password:
        return "Password is required"
    if len(password) < 6:
        return "Password must be at least 6 characters"
    return None


def validate_registration(data):
    email = data.get("email")
    password = data.get("password")
    # check required fields
    if not email or not password:
        return "Email and password are required"
    email_err = validate_email(email)
    if email_err:
        return email_err
    password_err = validate_password(password)
    if password_err:
        return password_err
    return None


def validate_login(data):
    email = data.get("email")
    password = data.get("password")
    # required fields validation
    if not email or not password:
        return "Email and password are required"
    email_err = validate_email(email)
    if email_err:
        return email_err
    return None
