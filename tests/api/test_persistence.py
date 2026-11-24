from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application import create_app
from database import get_db
from constants import TopicName
import clock
from datetime import datetime, timedelta

USER = {"username": "user1", "email": "user1@example.com", "password": "secret123"}


# -------------------------
# Helper functions
# -------------------------


def register_and_login(client, user=USER):
    client.post("/auth/register", json=user)

    response = client.post(
        "/auth/login", json={"email": user["email"], "password": user["password"]}
    )

    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_post_body(**overrides):
    body = {
        "title": "Test post title",
        "body": "This is a valid test post body.",
        "topics": [TopicName.TECH.value],
        "expires_at": (clock.get_current_time() + timedelta(days=1)).isoformat(),
    }

    # Convert datetime overrides to ISO format for JSON serialization.
    if "expires_at" in overrides and isinstance(overrides["expires_at"], datetime):
        overrides["expires_at"] = overrides["expires_at"].isoformat()

    body.update(overrides)
    return body


# -------------------------
# Data persistence tests
# -------------------------


def test_data_persists_after_reopening_application(tmp_path):
    database_path = tmp_path / "persistence-test.db"
    database_url = f"sqlite:///{database_path}"

    # First application instance
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    sessions = sessionmaker(bind=engine)

    app = create_app(db_engine=engine, session_factory=sessions)

    def override_db():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    with TestClient(app) as client:
        token = register_and_login(client, USER)

        response = client.post(
            "/posts/",
            json=create_post_body(),
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        post_id = response.json()["id"]

    # Close the first database engine.
    engine.dispose()

    # Second application instance, using the same database file.
    reopened_engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    reopened_sessions = sessionmaker(bind=reopened_engine)

    reopened_app = create_app(
        db_engine=reopened_engine,
        session_factory=reopened_sessions,
    )

    def override_reopened_db():
        with reopened_sessions() as session:
            yield session

    reopened_app.dependency_overrides[get_db] = override_reopened_db

    try:
        with TestClient(reopened_app) as reopened_client:
            # Log in again to verify the user record also persisted.
            token = register_and_login(reopened_client, USER)

            # Verify the post can be retrieved individually.
        response = reopened_client.get(
            f"/posts/{post_id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        assert response.json()["id"] == post_id
        assert response.json()["title"] == "Test post title"

        # Verify the post also appears in the post list.
        response = reopened_client.get(
            "/posts",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == post_id
        assert response.json()[0]["title"] == "Test post title"

    finally:
        reopened_engine.dispose()
