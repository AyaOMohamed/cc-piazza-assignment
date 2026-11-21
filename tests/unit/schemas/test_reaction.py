import pytest
from pydantic import ValidationError
from schemas.reaction import ReactionCreate, ReactionCountsResponse
from constants import ReactionName


def test_reaction_create_valid_like():
    reaction = ReactionCreate(reaction=ReactionName.LIKE)

    assert reaction.reaction == ReactionName.LIKE

def test_reaction_create_valid_dislike():
    reaction = ReactionCreate(reaction=ReactionName.DISLIKE)

    assert reaction.reaction == ReactionName.DISLIKE

def test_reaction_schema_rejects_invalid_type():
    with pytest.raises(ValidationError):
        ReactionCreate(reaction="Love")

def test_reaction_create_missing_reaction():
    with pytest.raises(ValidationError):
        ReactionCreate()

def test_reaction_counts_response_valid_data():
    response = ReactionCountsResponse(
        like_count=5,
        dislike_count=2
    )

    assert response.like_count == 5
    assert response.dislike_count == 2

def test_reaction_counts_response_missing_like_count():
    with pytest.raises(ValidationError):
        ReactionCountsResponse(dislike_count=2)

def test_reaction_counts_response_missing_dislike_count():
    with pytest.raises(ValidationError):
        ReactionCountsResponse(like_count=5)

def test_reaction_counts_response_serialization():
    response = ReactionCountsResponse(
        like_count=5,
        dislike_count=2
    )

    assert response.model_dump() == {
        "like_count": 5,
        "dislike_count": 2
    }