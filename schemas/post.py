from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from schemas.validators import validate_non_empty_text

# Request body for post creation.
class PostCreate(BaseModel):
    title: str
    body: str
    topics: list[str] = Field(min_length=1)
    expires_at: datetime

    _validate_title = field_validator("title")(
        validate_non_empty_text
    )

    _validate_body = field_validator("body")(
        validate_non_empty_text
    )

# Response body for a post .
class PostResponse(BaseModel):
    id: int
    author: str
    title: str
    body: str
    topics: list[str]
    created_at: datetime
    expires_at: datetime
    status: str
    like_count: int
    dislike_count: int
    comments: list[str]


    model_config = ConfigDict(from_attributes=True)


# Response builder
def build_post_response(post):
    now = datetime.now()

    likes = sum(
        1 for reaction in post.reactions
        if reaction.reaction_type.name == "like"
    )

    dislikes = sum(
        1 for reaction in post.reactions
        if reaction.reaction_type.name == "dislike"
    )

    return {
        "id": post.id,
        "author": post.user.username,
        "title": post.title,
        "body": post.body,
        "topics": [topic.name for topic in post.topics],
        "created_at": post.created_at,
        "expires_at": post.expires_at,
        "status": "Live" if post.expires_at > now else "Expired",
        "like_count": likes,
        "dislike_count": dislikes,
        "comments": [comment.body for comment in post.comments]
    }
