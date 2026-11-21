import models
from datetime import datetime
from database import get_db
from fastapi import APIRouter, Depends
from security import get_current_user
from schemas.post import PostResponse, build_post_response
from constants import TopicName
from sqlalchemy import func

router = APIRouter()


@router.get("/{topic}/most-active", response_model=list[PostResponse], status_code=201)
def most_active_live_post(
    topic: TopicName,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
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
    post = (
        db.query(models.Post)
        .filter(
            models.Post.topics.any(
                models.Topic.name == topic.value
            ),
            models.Post.expires_at > datetime.now()
        )
        .order_by(
            reaction_count.desc(),
            models.Post.created_at.desc()
        )
        .first()
    )

    if post is None:
        return []

    return [build_post_response(post)]