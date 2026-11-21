from datetime import datetime


def validate_non_empty_text(value: str) -> str:
    if not value.strip():
        raise ValueError("Text cannot be empty or contain only whitespace")

    return value


def validate_expiration(value):
    if value <= datetime.now():
        raise ValueError("Expiration date must be in the future")
    return value