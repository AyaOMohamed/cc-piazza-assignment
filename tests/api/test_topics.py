
from datetime import datetime, timedelta
import time

import pytest

from constants import TopicName, ReactionName, Status


USER_1 = {
    "username": "user1",
    "email": "user1@example.com",
    "password": "secret123",
}

USER_2 = {
    "username": "user2",
    "email": "user2@example.com",
    "password": "secret123",
}

USER_3 = {
    "username": "user3",
    "email": "user3@example.com",
    "password": "secret123",
}

# -------------------------
# Helper functions
# -------------------------

def register_and_login(client, user):
    client.post("/auth/register", json=user)

    response = client.post(
        "/auth/login",
        json={
            "email": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200
    return response.json()["access_token"]

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def create_post(client, token, title, expires_at=None):
    if expires_at is None:
        expires_at = datetime.now() + timedelta(days=1)

    response = client.post(
        "/posts/",
        json={
            "title": title,
            "body": "This is a test post body.",
            "topics": [TopicName.TECH.value],
            "expires_at": expires_at.isoformat(),
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    return response.json()

def react_to_post(client, token, post_id, reaction=ReactionName.LIKE.value):
    return client.put(
        f"/posts/{post_id}/reaction",
        json={"reaction": reaction},
        headers=auth_headers(token),
    )

# -------------------------
# Most-active post tests
# -------------------------

def test_most_active_returns_empty_list_when_no_live_posts(client):
    token = register_and_login(client, USER_1)

    response = client.get(
        f"/topics/{TopicName.TECH.value}/most-active",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json() == []

def test_most_active_returns_post_with_most_reactions(client):
    token_1 = register_and_login(client, USER_1)
    token_2 = register_and_login(client, USER_2)
    token_3 = register_and_login(client, USER_3)

    post_1 = create_post(client, token_1, "First post")
    post_2 = create_post(client, token_1, "Second post")

    # First post receives two reactions.
    assert react_to_post(client, token_2, post_1["id"]).status_code == 200
    assert react_to_post(client, token_3, post_1["id"]).status_code == 200

    # Second post receives one reaction.
    assert react_to_post(client, token_2, post_2["id"]).status_code == 200

    response = client.get(
        f"/topics/{TopicName.TECH.value}/most-active",
        headers=auth_headers(token_1),
    )

    assert response.status_code == 200

    posts = response.json()
    assert len(posts) == 1
    assert posts[0]["id"] == post_1["id"]
    assert posts[0]["like_count"] == 2

def test_most_active_returns_newest_post_when_reaction_counts_tie(client):
    token_1 = register_and_login(client, USER_1)
    token_2 = register_and_login(client, USER_2)

    post_1 = create_post(client, token_1, "Older post")

    # Ensure the posts have different creation timestamps.
    time.sleep(0.02)

    post_2 = create_post(client, token_1, "Newer post")

    assert react_to_post(client, token_2, post_1["id"]).status_code == 200
    assert react_to_post(client, token_2, post_2["id"]).status_code == 200

    response = client.get(
        f"/topics/{TopicName.TECH.value}/most-active",
        headers=auth_headers(token_1),
    )

    assert response.status_code == 200
    assert response.json()[0]["id"] == post_2["id"]

def test_most_active_excludes_expired_posts(client):
    token_1 = register_and_login(client, USER_1)
    token_2 = register_and_login(client, USER_2)

    expired_post = create_post(
        client,
        token_1,
        "Expired post",
        datetime.now() + timedelta(seconds=1),
    )

    # React while the post is still live.
    assert react_to_post(client, token_2, expired_post["id"]).status_code == 200

    live_post = create_post(client, token_1, "Live post")

    time.sleep(2)  # Ensure the first post is expired

    response = client.get(
        f"/topics/{TopicName.TECH.value}/most-active",
        headers=auth_headers(token_1),
    )

    assert response.status_code == 200
    posts = response.json()

    assert len(posts) == 1
    assert posts[0]["id"] == live_post["id"]


def test_most_active_returns_422_for_invalid_topic(client):
    token = register_and_login(client, USER_1)

    response = client.get(
        "/topics/InvalidTopic/most-active",
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_most_active_requires_authentication(client):
    response = client.get("/topics/Tech/most-active")

    assert response.status_code == 401
