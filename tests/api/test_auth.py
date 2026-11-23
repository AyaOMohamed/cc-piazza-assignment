import pytest
import jwt

from datetime import datetime, timedelta, timezone

from security import ALGORITHM, SECRET_KEY


USER = {"username": "user1", "email": "user1@example.com", "password": "secret123"}


# -------------------------
# Registration tests
# -------------------------

def test_register_valid_user(client):
    response = client.post("/auth/register", json=USER)

    assert response.status_code == 201
    assert response.json()["username"] == USER["username"]
    assert response.json()["email"] == USER["email"]

@pytest.mark.parametrize(
    "missing_field",
    ["password", "username", "email"]
)
def test_register_missing_field(client, missing_field):
    body = USER.copy()
    del body[missing_field]

    response = client.post("/auth/register", json=body)

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(error["loc"][-1] == missing_field for error in errors)

@pytest.mark.parametrize(
    "body, invalid_field",
    [
        ({**USER, "email": "not_valid_email"}, "email"),
        ({**USER, "username": "aa"}, "username"),
        ({**USER, "password": "1"}, "password"),
    ],
)
def test_invalid_registration_data_returns_422(
    client, body, invalid_field
):
    response = client.post("/auth/register", json=body)

    assert response.status_code == 422

    errors = response.json()["detail"]

    assert any(
        error["loc"][-1] == invalid_field
        for error in errors
    )

def test_duplicate_registration_returns_409(client):
    first = client.post("/auth/register", json=USER)

    assert first.status_code == 201

    duplicate = client.post("/auth/register", json=USER)

    assert duplicate.status_code == 409
    assert duplicate.json() == {
        "detail": "Email address is already registered"
    }

def test_register_password_is_not_returned(client):
    response = client.post("/auth/register", json=USER)

    assert response.status_code == 201
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()
    assert set(response.json()) == {"id", "username", "email"}


# -------------------------
# Login tests
# -------------------------

def test_login_with_valid_user(client):
    registered = client.post("/auth/register", json=USER)

    assert registered.status_code == 201

    login = client.post("/auth/login", json=USER)

    assert login.status_code == 200

    response_data = login.json()

    assert set(response_data) == {"access_token", "token_type"}
    assert response_data["token_type"] == "bearer"

    token = response_data["access_token"]

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )

    assert payload["sub"] == USER["email"]
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()

def test_login_unknown_email_returns_401(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "secret123"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password"
    }

def test_login_wrong_password_returns_401(client):
    client.post("/auth/register", json=USER)

    response = client.post(
        "/auth/login",
        json={
            "email": USER["email"],
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password"
    }

def test_login_invalid_email_returns_422(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "invalid",
            "password": "secret123"
        }
    )

    assert response.status_code == 422

@pytest.mark.parametrize("missing_field", ["password", "email"])
def test_login_missing_field_returns_422(client, missing_field):
    body = USER.copy()
    del body[missing_field]

    response = client.post("/auth/login", json=body)

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(error["loc"][-1] == missing_field for error in errors)
