import pytest
from pydantic import ValidationError
from schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse
)


def test_user_create_valid_data():
    user = UserCreate(
        username="Valid user name",
        email="validemail@example.com",
        password="validPassword"
    )

    assert user.username == "Valid user name"
    assert user.email == "validemail@example.com"
    assert user.password == "validPassword"

@pytest.mark.parametrize("username", ["", "   ", "ab", "a" * 51])
def test_user_create_invalid_username_length(username):
    with pytest.raises(ValidationError):
        UserCreate(
            username=username,
            email="validemail@example.com",
            password="validPassword"
        )

@pytest.mark.parametrize("email", ["", "   ", "invalid-email"])
def test_user_create_invalid_email(email):
    with pytest.raises(ValidationError):
        UserCreate(
            username="Valid user name",
            email=email,
            password="validPassword"
        )

def test_user_create_short_password():
    with pytest.raises(ValidationError):
        UserCreate(
            username="Valid user name",
            email="validemail@example.com",
            password="12345"
        )

def test_user_login_valid_data():
    user = UserLogin(
        email="validemail@example.com",
        password="validPassword"
    )

    assert user.email == "validemail@example.com"
    assert user.password == "validPassword"

def test_user_login_invalid_email():
    with pytest.raises(ValidationError):
        UserLogin(
            email="invalid-email",
            password="validPassword"
        )

def test_user_response_valid_data():
    user = UserResponse(
        id=1,
        username="Valid user name",
        email="validemail@example.com"
    )

    assert user.id == 1
    assert user.username == "Valid user name"
    assert user.email == "validemail@example.com"

def test_user_response_missing_id():
    with pytest.raises(ValidationError):
        UserResponse(
            username="Valid user name",
            email="validemail@example.com"
        )

def test_user_response_serialization():
    user = UserResponse(
        id=1,
        username="Valid user name",
        email="validemail@example.com"
    )

    assert user.model_dump() == {
        "id": 1,
        "username": "Valid user name",
        "email": "validemail@example.com"
    }

def test_token_response_valid_data():
    token = TokenResponse(
        access_token="example.jwt.token",
        token_type="bearer"
    )

    assert token.access_token == "example.jwt.token"
    assert token.token_type == "bearer"

def test_token_response_missing_access_token():
    with pytest.raises(ValidationError):
        TokenResponse(token_type="bearer")
