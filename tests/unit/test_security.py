import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import jwt
from fastapi import HTTPException

from security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    SECRET_KEY,
    ALGORITHM,
)

USER = {"username": "user1", "email": "user1@example.com", "password": "secret123"}

# -------------------------
# Password hashing tests
# -------------------------


def test_hash_password():
    hashed = hash_password(USER["password"])
    assert hashed != USER["password"]
    assert verify_password(USER["password"], hashed)
    assert not verify_password("wrong", hashed)


def test_verify_password_correct_password():
    hashed_password = hash_password(USER["password"])

    assert verify_password(USER["password"], hashed_password) is True


def test_verify_password_incorrect_password():
    hashed_password = hash_password(USER["password"])

    assert verify_password("wrongpassword", hashed_password) is False


def test_hash_password_generates_different_hashes():
    hash1 = hash_password(USER["password"])
    hash2 = hash_password(USER["password"])

    assert hash1 != hash2
    assert verify_password(USER["password"], hash1)
    assert verify_password(USER["password"], hash2)


# -------------------------
# Access token tests
# -------------------------


def test_create_access_token():
    token = create_access_token({"sub": USER["email"]})

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["sub"] == USER["email"]
    assert "exp" in payload


def test_create_access_token_expiration():
    token = create_access_token({"sub": USER["email"]})

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    expiration = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    expected_expiration = datetime.now(timezone.utc) + timedelta(minutes=30)

    # Allow a small difference due to execution time.
    assert abs((expiration - expected_expiration).total_seconds()) < 5


# -------------------------
# current user tests
# -------------------------


def test_get_current_user_valid_token():
    token = create_access_token({"sub": USER["email"]})

    credentials = SimpleNamespace(credentials=token)

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = USER

    result = get_current_user(credentials=credentials, db=db)

    assert result == USER
    db.query.assert_called_once()


def test_get_current_user_missing_credentials():
    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=None, db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


def test_get_current_user_invalid_token():
    credentials = SimpleNamespace(credentials="invalid-token")

    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials, db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


def test_get_current_user_expired_token():
    expired_token = jwt.encode(
        {
            "sub": USER["email"],
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    credentials = SimpleNamespace(credentials=expired_token)

    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials, db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


def test_get_current_user_missing_subject():
    token = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    credentials = SimpleNamespace(credentials=token)

    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials, db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


@pytest.mark.parametrize("sub", [1, ""])
def test_get_current_user_invalid_subject(sub):
    # Expected user's email in the token subject.
    token = create_access_token({"sub": sub})

    credentials = SimpleNamespace(credentials=token)

    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials, db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


def test_get_current_user_user_not_found():
    token = create_access_token({"sub": USER["email"]})

    credentials = SimpleNamespace(credentials=token)

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials, db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"
