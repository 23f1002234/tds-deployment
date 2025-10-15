# app/validator.py
import re
import os

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def validate_request(body: dict):
    required = [
        "email", "secret", "task", "round", "nonce",
        "brief", "checks", "evaluation_url"
    ]
    for f in required:
        if f not in body:
            return False, f"Missing required field: {f}"

    if not EMAIL_RE.match(body["email"]):
        return False, "Invalid email format"

    if not isinstance(body["checks"], list):
        return False, "checks must be an array"

    if body["round"] not in (1, 2):
        return False, "round must be 1 or 2"

    try:
        from urllib.parse import urlparse
        parsed = urlparse(body["evaluation_url"])
        if not (parsed.scheme and parsed.netloc):
            raise ValueError
    except Exception:
        return False, "Invalid evaluation_url"

    return True, None


def verify_secret(provided: str) -> bool:
    expected = os.getenv("MY_SECRET")
    return bool(expected) and provided == expected
