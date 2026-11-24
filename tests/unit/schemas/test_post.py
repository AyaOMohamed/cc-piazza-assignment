import pytest
from types import SimpleNamespace
from datetime import datetime, timedelta
from pydantic import ValidationError
from schemas.post import PostCreate, PostResponse, build_post_response
from constants import TopicName, ReactionName, Status


def test_post_create_valid_data():
    data = PostCreate(
        title="Valid post title",
        body="Valid post body",
        topics=[TopicName.TECH],
        expires_at=datetime(2026, 12, 1, 12, 0),
    )

    assert data.title == "Valid post title"
    assert data.body == "Valid post body"
    assert data.topics == [TopicName.TECH]


@pytest.mark.parametrize("title", ["", "   "])
def test_post_create_rejects_whitespace_title(title):
    with pytest.raises(ValidationError):
        PostCreate(
            title=title,
            body="Valid post body",
            topics=[TopicName.TECH],
            expires_at=datetime(2026, 12, 1, 12, 0),
        )


@pytest.mark.parametrize("body", ["", "   "])
def test_post_create_rejects_whitespace_body(body):
    with pytest.raises(ValidationError):
        PostCreate(
            title="Valid post title",
            body=body,
            topics=[TopicName.TECH],
            expires_at=datetime(2026, 12, 1, 12, 0),
        )


@pytest.mark.parametrize("topics", [[], ["Invalid"], [TopicName.TECH, "Invalid"]])
def test_post_create_rejects_invalid_topic(topics):
    with pytest.raises(ValidationError):
        PostCreate(
            title="Python discussion",
            body="Valid post body",
            topics=topics,
            expires_at=datetime(2026, 12, 1, 12, 0),
        )


def test_post_create_missing_expires_at():
    with pytest.raises(ValidationError):
        PostCreate(
            title="Valid post title", body="Valid post body", topics=[TopicName.TECH]
        )


def test_post_create_invalid_expires_at():
    with pytest.raises(ValidationError):
        PostCreate(
            title="Valid post title",
            body="Valid post body",
            topics=[TopicName.TECH],
            expires_at=datetime.now() - timedelta(days=1),
        )


def test_post_response_valid_data():
    post = PostResponse(
        id=1,
        author="Valid user",
        title="Valid post title",
        body="Valid post body",
        topics=[TopicName.TECH],
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=1),
        status=Status.LIVE,
        like_count=2,
        dislike_count=1,
        comments=["First comment"],
    )

    assert post.id == 1
    assert post.author == "Valid user"
    assert post.title == "Valid post title"
    assert post.topics == [TopicName.TECH]
    post.status = Status.LIVE
    assert post.like_count == 2
    assert post.dislike_count == 1


def test_post_response_missing_required_field():
    with pytest.raises(ValidationError):
        PostResponse(
            author="Valid user",
            title="Valid post title",
            body="Valid post body",
            topics=[TopicName.TECH],
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=1),
            status=Status.LIVE,
            like_count=2,
            dislike_count=1,
            comments=["First comment"],
        )


def test_post_response_serialization():
    now = datetime.now()

    post = PostResponse(
        id=1,
        author="Valid user",
        title="Valid post title",
        body="Valid post body",
        topics=[TopicName.TECH],
        created_at=now,
        expires_at=now + timedelta(days=1),
        status=Status.LIVE,
        like_count=2,
        dislike_count=1,
        comments=["First comment"],
    )

    result = post.model_dump()

    assert result["id"] == 1
    assert result["author"] == "Valid user"
    assert result["topics"] == [TopicName.TECH]
    assert result["like_count"] == 2
    assert result["dislike_count"] == 1


def test_build_post_response():
    now = datetime.now()

    post = SimpleNamespace(
        id=1,
        user=SimpleNamespace(username="Valid user"),
        title="Valid post title",
        body="Valid post body",
        topics=[SimpleNamespace(name=TopicName.TECH)],
        created_at=now,
        expires_at=now + timedelta(days=1),
        reactions=[
            SimpleNamespace(reaction_type=SimpleNamespace(name=ReactionName.LIKE)),
            SimpleNamespace(reaction_type=SimpleNamespace(name=ReactionName.LIKE)),
            SimpleNamespace(reaction_type=SimpleNamespace(name=ReactionName.DISLIKE)),
        ],
        comments=[SimpleNamespace(body="First comment")],
    )

    result = build_post_response(post)

    assert result.id == 1
    assert result.author == "Valid user"
    assert result.topics == [TopicName.TECH]
    assert result.status == Status.LIVE
    assert result.like_count == 2
    assert result.dislike_count == 1
    assert result.comments == ["First comment"]


def test_build_post_response_expired_post():
    now = datetime.now()

    post = SimpleNamespace(
        id=1,
        user=SimpleNamespace(username="Valid user"),
        title="Expired post",
        body="This post has expired.",
        topics=[],
        created_at=now - timedelta(days=2),
        expires_at=now - timedelta(days=1),
        reactions=[],
        comments=[],
    )

    result = build_post_response(post)

    assert result.status == Status.EXPIRED
    assert result.like_count == 0
    assert result.dislike_count == 0
