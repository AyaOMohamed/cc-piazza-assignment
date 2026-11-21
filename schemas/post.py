from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from schemas.validators import validate_non_empty_text, validate_expiration
from constants import TopicName, ReactionName, Status


# Request body for post creation.
class PostCreate(BaseModel):
    title: str
    body: str
    topics: list[TopicName] = Field(min_length=1)
    expires_at: datetime

    _validate_title = field_validator("title")(
        validate_non_empty_text
    )

    _validate_body = field_validator("body")(
        validate_non_empty_text
    )
    
    _validate_expires_at = field_validator("expires_at")(
        validate_expiration
    )


# Response body for a post .
class PostResponse(BaseModel):
    id: int
    author: str
    title: str
    body: str
    topics: list[TopicName]
    created_at: datetime
    expires_at: datetime
    status: Status
    like_count: int
    dislike_count: int
    comments: list[str]


    model_config = ConfigDict(from_attributes=True)


# Response builder
def build_post_response(post) -> PostResponse:
    now = datetime.now()

    likes = sum(
        1 for reaction in post.reactions
        if reaction.reaction_type.name == ReactionName.LIKE
    )

    dislikes = sum(
        1 for reaction in post.reactions
        if reaction.reaction_type.name == ReactionName.DISLIKE
    )

    return PostResponse(
        id=post.id,
        author=post.user.username,
        title=post.title,
        body=post.body,
        topics=[topic.name for topic in post.topics],
        created_at=post.created_at,
        expires_at=post.expires_at,
        status=Status.LIVE if post.expires_at > now else Status.EXPIRED,
        like_count=likes,
        dislike_count=dislikes,
        comments=[comment.body for comment in post.comments]
    )