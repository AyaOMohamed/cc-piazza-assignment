import pytest
from pydantic import ValidationError
from schemas.comment import CommentCreate, CommentResponse


def test_comment_create_valid_data():
    data = CommentCreate(body="Valid comment body")

    assert data.body == "Valid comment body"


@pytest.mark.parametrize("body", ["", "   "])
def test_comment_create_rejects_whitespace_body(body):
    with pytest.raises(ValidationError):
        CommentCreate(body=body)


def test_comment_create_missing_body():
    with pytest.raises(ValidationError):
        CommentCreate()


def test_comment_response_valid_data():
    comment = CommentResponse(id=1, user_id=1, post_id=2, body="Valid comment body")

    assert comment.id == 1
    assert comment.user_id == 1
    assert comment.post_id == 2
    assert comment.body == "Valid comment body"


def test_comment_response_missing_id():
    with pytest.raises(ValidationError):
        CommentResponse(user_id=1, post_id=2, body="Valid comment body")


def test_comment_response_serialization():
    comment = CommentResponse(id=1, user_id=1, post_id=2, body="Valid comment body")

    assert comment.model_dump() == {
        "id": 1,
        "user_id": 1,
        "post_id": 2,
        "body": "Valid comment body",
    }
