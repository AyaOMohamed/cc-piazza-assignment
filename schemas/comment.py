import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from app.schemas.validators import validate_non_empty_text

# Request body for comment creation.
class CommentCreate(BaseModel):
    user_id: int
    post_id: int
    body: str

    _validate_body = field_validator("body")(
        validate_non_empty_text
    )
