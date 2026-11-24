from datetime import datetime
import clock

def validate_non_empty_text(value: str) -> str:
    if not value.strip():
        raise ValueError("Text cannot be empty or contain only whitespace")

    return value


def validate_expiration(value):
    if value <= clock.get_current_time():
        raise ValueError("Expiration date must be in the future")
    return value