import re

EMAIL_REGEX = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

def validate_registration(data):
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirm_password")
    #check required fields
    if not email or not password or not confirm_password:
        return "Email,password and confirm password are required"
    #email format validation
    if not re.match(EMAIL_REGEX, email):
        return "Invalid email format"
    #password match validation
    if password != confirm_password:
        return "Passwords do not match"
    #password length validation
    if len(password) < 6:
        return "Password must be at least 6 characters"
    return None


def validate_login(data):
    email = data.get("email")
    password = data.get("password")
    #required fields validation
    if not email or not password:
        return "Email and password are required"
    #email format validation
    if not re.match(EMAIL_REGEX, email):
        return "Invalid email format"
    return None
