from backend.extensions import bcrypt


def hash_password(plain_password: str) -> str:
    return bcrypt.generate_password_hash(plain_password).decode("utf-8")


def check_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.check_password_hash(hashed_password, plain_password)
