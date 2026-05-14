from __future__ import annotations

from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    """Generate a secure hash for the given password."""
    return generate_password_hash(password, method="pbkdf2:sha256")


def check_password(password_hash: str, password: str) -> bool:
    """Verify a password against its hash."""
    return check_password_hash(password_hash, password)


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.
    Returns (is_valid, error_message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    return True, None