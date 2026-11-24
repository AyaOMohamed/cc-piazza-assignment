
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from constants import TopicName, Status, ReactionName


# -------------------------
# Test users and helpers
# -------------------------

OLGA = {
    "username": "Olga",
    "email": "olga@example.com",
    "password": "secret123",
}

NICK = {
    "username": "Nick",
    "email": "nick@example.com",
    "password": "secret123",
}

MARY = {
    "username": "Mary",
    "email": "mary@example.com",
    "password": "secret123",
}

NESTOR = {
    "username": "Nestor",
    "email": "nestor@example.com",
    "password": "secret123",
}

def register_user(client, user):
    response = client.post("/auth/register", json=user)
    assert response.status_code == 201
    return response.json()

def login_user(client, user):
    response = client.post(
        "/auth/login",
        json={
            "email": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200
    assert response.json()["access_token"]

    return response.json()["access_token"]

def register_and_login_users(client):
    users = {
        "olga": OLGA,
        "nick": NICK,
        "mary": MARY,
        "nestor": NESTOR,
    }

    tokens = {}

    for name, user in users.items():
        register_user(client, user)
        tokens[name] = login_user(client, user)

    return tokens

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def create_post(client, token, title, topic=TopicName.TECH.value, expires_at=None):
    if expires_at is None:
        expires_at = datetime.now() + timedelta(days=1)

    response = client.post(
        "/posts/",
        json={
            "title": title,
            "body": f"Body for {title}",
            "topics": [topic],
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

def add_comment(client, token, post_id, body):
    return client.post(
        f"/posts/{post_id}/comments",
        json={"body": body},
        headers=auth_headers(token),
    )

def get_post(client, token, post_id):
    return client.get(
        f"/posts/{post_id}",
        headers=auth_headers(token),
    )

def get_posts(client, token, topic=None, status=None):
    params = {}

    if topic:
        params["topic"] = topic

    if status:
        params["status"] = status

    return client.get(
        "/posts/",
        params=params,
        headers=auth_headers(token),
    )

# ----------------------------------
# TC01–TC02: Registration and login
# ----------------------------------

def test_four_users_register_and_login(client):
    users = [OLGA, NICK, MARY, NESTOR]
    tokens = {}

    for user in users:
        registration = register_user(client, user)
        assert registration["username"] == user["username"]

        tokens[user["username"]] = login_user(client, user)

    assert len(tokens) == 4

# ----------------------------------
# TC03–TC13 and TC20: Tech scenario
# ----------------------------------

def test_tech_discussion_scenario(client):
    tokens = register_and_login_users(client)

    olga = tokens["olga"]
    nick = tokens["nick"]
    mary = tokens["mary"]
    nestor = tokens["nestor"]

    # TC03: Olga cannot access a business endpoint without a token.
    response = client.get("/posts/")
    assert response.status_code == 401

    # TC04–TC06: Olga, Nick and Mary create Tech posts.
    olga_post = create_post(client, olga, "Olga's Tech post")
    nick_post = create_post(client, nick, "Nick's Tech post")
    mary_post = create_post(client, mary, "Mary's Tech post")

    # TC07: Browsing Tech returns three posts with no reactions or comments.
    response = get_posts(client, olga, topic=TopicName.TECH.value)

    assert response.status_code == 200

    posts = response.json()
    assert len(posts) == 3

    for post in posts:
        assert post["like_count"] == 0
        assert post["dislike_count"] == 0
        assert post["comments"] == []

    # TC08: Nick and Olga like Mary's post.
    assert react_to_post(client, nick, mary_post["id"]).status_code == 200
    assert react_to_post(client, olga, mary_post["id"]).status_code == 200

    # TC09: Nestor likes Nick's post and dislikes Mary's post.
    assert react_to_post(client, nestor, nick_post["id"]).status_code == 200

    assert react_to_post(
        client, nestor, mary_post["id"], ReactionName.DISLIKE.value
    ).status_code == 200

    # TC10: Verify reaction counts.
    response = get_post(client, olga, mary_post["id"])
    assert response.status_code == 200

    mary_data = response.json()
    assert mary_data["like_count"] == 2
    assert mary_data["dislike_count"] == 1

    response = get_post(client, olga, nick_post["id"])
    assert response.status_code == 200

    nick_data = response.json()
    assert nick_data["like_count"] == 1
    assert nick_data["dislike_count"] == 0

    # TC11: Mary cannot react to her own post.
    response = react_to_post(client, mary, mary_post["id"])
    assert response.status_code == 403

    # TC12: Nick and Olga each add at least two comments to Mary's post.
    assert add_comment(
        client, nick, mary_post["id"], "Nick's first comment"
    ).status_code == 201

    assert add_comment(
        client, nick, mary_post["id"], "Nick's second comment"
    ).status_code == 201

    assert add_comment(
        client, olga, mary_post["id"], "Olga's first comment"
    ).status_code == 201

    assert add_comment(
        client, olga, mary_post["id"], "Olga's second comment"
    ).status_code == 201

    # TC13: Browsing reflects the correct counts and comments.
    response = get_posts(client, olga, topic=TopicName.TECH.value)

    assert response.status_code == 200

    mary_data = next(
        post for post in response.json()
        if post["id"] == mary_post["id"]
    )

    assert mary_data["like_count"] == 2
    assert mary_data["dislike_count"] == 1
    assert len(mary_data["comments"]) == 4

    # TC20: Mary's post is the most-active Tech post.
    response = client.get(
        f"/topics/{TopicName.TECH.value}/most-active",
        headers=auth_headers(olga),
    )

    assert response.status_code == 200

    most_active = response.json()

    assert len(most_active) == 1
    assert most_active[0]["id"] == mary_post["id"]

# -------------------------------------------
# TC14–TC18: Health post and expiry scenario
# -------------------------------------------

def test_health_post_expiry_scenario(client):
    tokens = register_and_login_users(client)

    nestor = tokens["nestor"]
    mary = tokens["mary"]

    fixed_time = datetime(2026, 11, 24, 12, 0, 0)

    # Freeze the application clock while creating and commenting.
    with (
        patch("routers.posts.clock.get_current_time", return_value=fixed_time),
        patch("schemas.post.clock.get_current_time", return_value=fixed_time),
    ):
        # TC14: Nestor creates a Health post.
        health_post = create_post(
            client,
            nestor,
            "Nestor's Health post",
            topic="Health",
            expires_at=fixed_time + timedelta(minutes=5),
        )

        # TC15: Health browsing returns the appropriate post.
        response = get_posts(
            client,
            mary,
            topic=TopicName.HEALTH.value,
            status=Status.LIVE.value,
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == health_post["id"]

        # TC16: Mary comments while the Health post is live.
        comment_response = add_comment(
            client,
            mary,
            health_post["id"],
            "Mary's comment on the Health post",
        )

        assert comment_response.status_code == 201

    # Advance the application clock beyond the expiry.
    expired_time = fixed_time + timedelta(minutes=10)

    with (
        patch("routers.posts.clock.get_current_time", return_value=expired_time),
        patch("routers.topics.clock.get_current_time", return_value=expired_time),
        patch("schemas.post.clock.get_current_time", return_value=expired_time),
    ):
        # TC17: Mary cannot react after the post expires.
        response = react_to_post(
            client,
            mary,
            health_post["id"],
        )

        assert response.status_code == 409

        # TC18: The expired post remains readable with its comment.
        response = get_post(client, mary, health_post["id"])

        assert response.status_code == 200

        post_data = response.json()

        assert post_data["id"] == health_post["id"]
        assert post_data["status"] == Status.EXPIRED.value
        assert "Mary's comment on the Health post" in post_data["comments"]


# --------------------------------------------------
# TC19: Empty expired Sport browsing
# --------------------------------------------------

def test_expired_sport_browsing_returns_empty_list(client):
    tokens = register_and_login_users(client)
    mary = tokens["mary"]

    response = get_posts(
        client,
        mary,
        topic=TopicName.SPORT.value,
        status=Status.EXPIRED.value,
    )

    assert response.status_code == 200
    assert response.json() == []