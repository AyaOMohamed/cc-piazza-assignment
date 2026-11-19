def validate_non_empty_text(value: str) -> str:
    if not value.strip():
        raise ValueError("Text cannot be empty or contain only whitespace")

    return value