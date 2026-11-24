import models
from database import get_db
from fastapi import APIRouter, Depends
from security import get_current_user
from schemas.post import PostResponse, build_post_response
from constants import TopicName
from sqlalchemy import func
from sqlalchemy.orm import Session
import clock

router = APIRouter()


@router.get("/{topic}/most-active", response_model=list[PostResponse], status_code=200)
def most_active_live_post(
    topic: TopicName,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Inner count query
    # Count all reactions for each post,cregardless of the reaction type
    reaction_count = (
        db.query(func.count(models.Reaction.post_id))
        .filter(models.Reaction.post_id == models.Post.id)
        .correlate(models.Post)
        .scalar_subquery()
    )

    # Outer select query
    # Find the most-active live post in the selected topic
    # Rank posts by reaction count, using creation timestamp and post ID to resolve ties.
    post = (
        db.query(models.Post)
        .filter(
            models.Post.topics.any(models.Topic.name == topic.value),
            models.Post.expires_at > clock.get_current_time(),
        )
        .order_by(
            reaction_count.desc(), models.Post.created_at.desc(), models.Post.id.asc()
        )
        .first()
    )

    if post is None:
        return []

    return [build_post_response(post)]
