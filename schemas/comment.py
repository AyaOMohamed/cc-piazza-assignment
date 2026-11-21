import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from schemas.validators import validate_non_empty_text


# Request body for comment creation.
class CommentCreate(BaseModel):
    body: str

    _validate_body = field_validator("body")(
        validate_non_empty_text
    )

# Response body for comment creation.
class CommentResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    body: str

    model_config = ConfigDict(from_attributes=True)