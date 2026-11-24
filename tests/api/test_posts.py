import pytest
from datetime import datetime, timedelta

import clock

from constants import TopicName, Status, ReactionName


USER = {
    "username": "user1",
    "email": "user1@example.com",
    "password": "secret123"
}

OTHER_USER = {
    "username": "user2",
    "email": "user2@example.com",
    "password": "secret123"
}


# -------------------------
# Helper functions
# -------------------------

def register_and_login(client, user=USER):
    client.post("/auth/register", json=user)

    response = client.post(
        "/auth/login",
        json={
            "email": user["email"],
            "password": user["password"]
        }
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
        "expires_at": (
            clock.get_current_time() + timedelta(days=1)
        ).isoformat()
    }

    # Convert datetime overrides to ISO format for JSON serialization.
    if "expires_at" in overrides and isinstance(overrides["expires_at"], datetime):
        overrides["expires_at"] = overrides["expires_at"].isoformat()

    body.update(overrides)
    return body

# -------------------------
# Create post tests
# -------------------------

def test_create_post_success(client):
    token = register_and_login(client)

    response = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(token)
    )

    assert response.status_code == 201, response.json()

    data = response.json()

    assert data["id"] is not None
    assert data["author"] == USER["username"]
    assert data["title"] == "Test post title"
    assert data["body"] == "This is a valid test post body."
    assert data["topics"] == [TopicName.TECH.value]
    assert data["like_count"] == 0
    assert data["dislike_count"] == 0
    assert data["comments"] == []
    assert data["status"] == Status.LIVE.value


@pytest.mark.parametrize(
    "field, value",
    [
        ("title", ""),
        ("title", "   "),
        ("body", ""),
        ("body", "   "),
        ("topics", []),
        ("topics", ["Invalid"]),
        ("expires_at", datetime(2000, 1, 1).isoformat()),
        ("expires_at", "invalid-date"),
    ]
)
def test_create_post_invalid_data_returns_422(client, field, value):
    token = register_and_login(client)

    response = client.post(
        "/posts/",
        json=create_post_body(**{field: value}),
        headers=auth_headers(token)
    )

    assert response.status_code == 422

@pytest.mark.parametrize(
    "missing_field",
    ["title", "body", "topics", "expires_at"]
)
def test_create_post_missing_field_returns_422(client, missing_field):
    token = register_and_login(client)

    body = create_post_body()
    del body[missing_field]

    response = client.post(
        "/posts/",
        json=body,
        headers=auth_headers(token)
    )

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(error["loc"][-1] == missing_field for error in errors)

def test_create_post_requires_authentication(client):
    response = client.post(
        "/posts/",
        json=create_post_body()
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

# -------------------------
# Get posts tests
# -------------------------

def test_get_posts_success(client):
    token = register_and_login(client)

    client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(token)
    )

    response = client.get(
        "/posts/",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Test post title"

def test_get_posts_filter_by_topic(client):
    token = register_and_login(client)

    client.post(
        "/posts/",
        json=create_post_body(topics=[TopicName.TECH.value]),
        headers=auth_headers(token)
    )

    client.post(
        "/posts/",
        json=create_post_body(
            title="Health post",
            topics=[TopicName.HEALTH.value]
        ),
        headers=auth_headers(token)
    )

    response = client.get(
        f"/posts/?topic={TopicName.TECH.value}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["topics"] == [TopicName.TECH.value]

def test_get_posts_filter_by_live_status(client, mock_clock):
    token = register_and_login(client)

    client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(token)
    )

    client.post(
        "/posts/",
        json=create_post_body(
            title="Expired post",
            expires_at=(
                clock.get_current_time() + timedelta(seconds=1)
            ).isoformat()
        ),
        headers=auth_headers(token)
    )

    # Advance time beyond the second post's expiry.
    mock_clock[0] += timedelta(seconds=2)

    response = client.get(
        f"/posts/?status={Status.LIVE.value}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == Status.LIVE.value
    assert response.json()[0]["title"] == "Test post title"

def test_get_posts_filter_by_expired_status(client, mock_clock):
    token = register_and_login(client)

    client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(token)
    )

    client.post(
        "/posts/",
        json=create_post_body(
            title="Expired post",
            expires_at=(
                clock.get_current_time() + timedelta(seconds=1)
            ).isoformat()
        ),
        headers=auth_headers(token)
    )

    # Advance time beyond the second post's expiry.
    mock_clock[0] += timedelta(seconds=2)

    response = client.get(
        f"/posts/?status={Status.EXPIRED.value}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == Status.EXPIRED.value
    assert response.json()[0]["title"] == "Expired post"

def test_get_posts_invalid_topic_returns_422(client):
    token = register_and_login(client)

    response = client.get(
        "/posts/?topic=InvalidTopic",
        headers=auth_headers(token)
    )

    assert response.status_code == 422

def test_get_posts_invalid_status_returns_422(client):
    token = register_and_login(client)

    response = client.get(
        "/posts/?status=InvalidStatus",
        headers=auth_headers(token)
    )

    assert response.status_code == 422

def test_get_posts_requires_authentication(client):
    response = client.get("/posts/")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

# -------------------------
# Get single post tests
# -------------------------

def test_get_post_success(client):
    token = register_and_login(client)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(token)
    )
    post_id = created.json()["id"]

    response = client.get(
        f"/posts/{post_id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["id"] == post_id
    assert response.json()["title"] == "Test post title"

def test_get_post_not_found(client):
    token = register_and_login(client)

    response = client.get(
        "/posts/999",
        headers=auth_headers(token)
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}

def test_get_post_invalid_id_returns_422(client):
    token = register_and_login(client)

    response = client.get(
        "/posts/invalid",
        headers=auth_headers(token)
    )

    assert response.status_code == 422

def test_get_post_requires_authentication(client):
    token = register_and_login(client)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(token)
    )
    post_id = created.json()["id"]

    response = client.get(f"/posts/{post_id}")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

# -------------------------
# Reaction tests
# -------------------------

def test_add_like_to_post(client):
    author_token = register_and_login(client, USER)
    other_token = register_and_login(client, OTHER_USER)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(author_token)
    )
    post_id = created.json()["id"]

    response = client.put(
        f"/posts/{post_id}/reaction",
        json={"reaction": ReactionName.LIKE.value},
        headers=auth_headers(other_token)
    )

    assert response.status_code == 200
    assert response.json() == {
        "like_count": 1,
        "dislike_count": 0
    }

def test_add_dislike_to_post(client):
    author_token = register_and_login(client, USER)
    other_token = register_and_login(client, OTHER_USER)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(author_token)
    )
    post_id = created.json()["id"]

    response = client.put(
        f"/posts/{post_id}/reaction",
        json={"reaction": ReactionName.DISLIKE.value},
        headers=auth_headers(other_token)
    )

    assert response.status_code == 200
    assert response.json() == {
        "like_count": 0,
        "dislike_count": 1
    }

def test_replace_like_with_dislike(client):
    author_token = register_and_login(client, USER)
    other_token = register_and_login(client, OTHER_USER)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(author_token)
    )
    post_id = created.json()["id"]

    client.put(
        f"/posts/{post_id}/reaction",
        json={"reaction": ReactionName.LIKE.value},
        headers=auth_headers(other_token)
    )

    response = client.put(
        f"/posts/{post_id}/reaction",
        json={"reaction": ReactionName.DISLIKE.value},
        headers=auth_headers(other_token)
    )

    assert response.status_code == 200
    assert response.json() == {
        "like_count": 0,
        "dislike_count": 1
    }

def test_reaction_post_not_found(client):
    token = register_and_login(client)

    response = client.put(
        "/posts/999/reaction",
        json={"reaction": ReactionName.LIKE.value},
        headers=auth_headers(token)
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}

def test_reaction_expired_post_returns_409(client, mock_clock):
    author_token = register_and_login(client, USER)
    other_token = register_and_login(client, OTHER_USER)

    created = client.post(
        "/posts/",
        json=create_post_body(
            expires_at=(
                clock.get_current_time() + timedelta(seconds=1)
            ).isoformat()
        ),
        headers=auth_headers(author_token)
    )
    assert created.status_code == 201, created.json()
    post_id = created.json()["id"]

    # Advance time beyond the post's expiry.
    mock_clock[0] += timedelta(seconds=2)

    response = client.put(
        f"/posts/{post_id}/reaction",
        json={"reaction": ReactionName.LIKE.value},
        headers=auth_headers(other_token)
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot react to an expired post"

def test_author_cannot_react_to_own_post(client):
    token = register_and_login(client)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(token)
    )
    post_id = created.json()["id"]

    response = client.put(
        f"/posts/{post_id}/reaction",
        json={"reaction": ReactionName.LIKE.value},
        headers=auth_headers(token)
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You cannot react to your own post"
    )

def test_invalid_reaction_returns_422(client):
    author_token = register_and_login(client, USER)
    other_token = register_and_login(client, OTHER_USER)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(author_token)
    )
    post_id = created.json()["id"]

    response = client.put(
        f"/posts/{post_id}/reaction",
        json={"reaction": "Love"},
        headers=auth_headers(other_token)
    )

    assert response.status_code == 422

def test_reaction_missing_field_returns_422(client):
    token = register_and_login(client)

    response = client.put(
        "/posts/1/reaction",
        json={},
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_reaction_requires_authentication(client):
    author_token = register_and_login(client, USER)
    other_token = register_and_login(client, OTHER_USER)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(author_token)
    )
    post_id = created.json()["id"]

    response = client.put(
        f"/posts/{post_id}/reaction",
        json={"reaction": ReactionName.LIKE.value}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

# -------------------------
# Comments tests
# -------------------------

def test_add_comment_success(client):
    token = register_and_login(client)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(token)
    )
    post_id = created.json()["id"]

    response = client.post(
        f"/posts/{post_id}/comments",
        json={"body": "This is a valid comment."},
        headers=auth_headers(token)
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["user_id"] is not None
    assert data["post_id"] == post_id
    assert data["body"] == "This is a valid comment."

@pytest.mark.parametrize(
    "body",
    ["", "   "]
)
def test_add_comment_invalid_body_returns_422(client, body):
    token = register_and_login(client)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(token)
    )
    post_id = created.json()["id"]

    response = client.post(
        f"/posts/{post_id}/comments",
        json={"body": body},
        headers=auth_headers(token)
    )

    assert response.status_code == 422

def test_add_comment_missing_body_returns_422(client):
    token = register_and_login(client)

    created = client.post(
        "/posts/",
        json=create_post_body(),
        headers=auth_headers(token)
    )
    post_id = created.json()["id"]

    response = client.post(
        f"/posts/{post_id}/comments",
        json={},
        headers=auth_headers(token)
    )

    assert response.status_code == 422

def test_add_comment_post_not_found(client):
    token = register_and_login(client)

    response = client.post(
        "/posts/999/comments",
        json={"body": "This is a valid comment."},
        headers=auth_headers(token)
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}

def test_add_comment_expired_post_returns_409(client, mock_clock):
    token = register_and_login(client)

    created = client.post(
        "/posts/",
        json=create_post_body(
            expires_at=(
                clock.get_current_time() + timedelta(seconds=1)
            ).isoformat()
        ),
        headers=auth_headers(token)
    )
    assert created.status_code == 201, created.json()
    post_id = created.json()["id"]

    # Advance time beyond the post's expiry.
    mock_clock[0] += timedelta(seconds=2)

    response = client.post(
        f"/posts/{post_id}/comments",
        json={"body": "This is a valid comment."},
        headers=auth_headers(token)
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot comment on an expired post"

def test_add_comment_requires_authentication(client):
    response = client.post(
        "/posts/1/comments",
        json={"body": "This is a valid comment."}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

# -------------------------
# Expiry boundary tests
# -------------------------

def test_post_is_live_immediately_before_expiry(client, mock_clock):
    token = register_and_login(client, USER)
    expiry_time = mock_clock[0] + timedelta(days=1)

    response = client.post(
        "/posts/",
        json=create_post_body(expires_at=expiry_time),
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    post_id = response.json()["id"]

    mock_clock[0] = expiry_time - timedelta(microseconds=1)

    response = client.get(
        f"/posts/{post_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == Status.LIVE.value

def test_post_is_expired_exactly_at_expiry(client, mock_clock):
    token = register_and_login(client, USER)
    expiry_time = mock_clock[0] + timedelta(days=1)

    response = client.post(
        "/posts/",
        json=create_post_body(expires_at=expiry_time),
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    post_id = response.json()["id"]

    mock_clock[0] = expiry_time

    response = client.get(
        f"/posts/{post_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == Status.EXPIRED.value

def test_post_remains_expired_after_expiry(client, mock_clock):
    token = register_and_login(client, USER)
    expiry_time = mock_clock[0] + timedelta(days=1)

    response = client.post(
        "/posts/",
        json=create_post_body(expires_at=expiry_time),
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    post_id = response.json()["id"]

    mock_clock[0] = expiry_time + timedelta(microseconds=1)

    response = client.get(
        f"/posts/{post_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == Status.EXPIRED.value