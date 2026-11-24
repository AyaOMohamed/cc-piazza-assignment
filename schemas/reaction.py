from pydantic import BaseModel
from constants import ReactionName


class ReactionCreate(BaseModel):
    reaction: ReactionName


class ReactionCountsResponse(BaseModel):
    like_count: int
    dislike_count: int
