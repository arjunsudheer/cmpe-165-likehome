from email_validator import EmailNotValidError, validate_email


def is_valid_email_format(email: str) -> bool:
    try:
        parsed = validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return False

    top_level_domain = parsed.domain.rsplit(".", maxsplit=1)[-1]
    return len(top_level_domain) >= 2


def validate_registration(data):
    email = data.get("email")
    password = data.get("password")
    # check required fields
    if not email or not password:
        return "Email and password are required"
    # email format validation
    if not is_valid_email_format(email):
        return "Invalid email format"
    # password length validation
    if len(password) < 6:
        return "Password must be at least 6 characters"
    return None


def validate_login(data):
    email = data.get("email")
    password = data.get("password")
    # required fields validation
    if not email or not password:
        return "Email and password are required"
    # email format validation
    if not is_valid_email_format(email):
        return "Invalid email format"
    return None
