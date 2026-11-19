from datetime import datetime
import models
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from security import get_current_user
from schemas.post import PostCreate, PostResponse, build_post_response
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/posts")


@router.post("/", response_model=PostResponse, status_code=201)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Retrieve the requested topics
    db_topics = (
        db.query(models.Topic)
        .filter(models.Topic.name.in_(post.topics))
        .all()
    )

    # Check that all requested topics exist
    if len(db_topics) != len(set(post.topics)):
        raise HTTPException(
            status_code=422,
            detail="One or more topics are invalid"
        )

    # Create the post
    db_post = models.Post(
        user_id=current_user.id,
        title=post.title,
        body=post.body,
        created_at=datetime.now(),
        expires_at=post.expires_at,
        topics=db_topics
    )

    # Save post and topic associations in one transaction
    db.add(db_post)

    try:
        db.commit()
        db.refresh(db_post)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Could not create post",
                "error": str(exc.orig)
            }
        )

    return build_post_response(db_post)


@router.get("/", response_model=list[PostResponse], status_code=200)
def get_posts(
    topic: str | None = Query(default=None),
    status: Literal["Live", "Expired"] | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Start with all posts
    query = db.query(models.Post)

    # Filter by topic
    if topic:
        query = query.filter(
            models.Post.topics.any(models.Topic.name == topic)
        )

    # Filter by status
    now = datetime.now()

    if status == "Live":
        query = query.filter(models.Post.expires_at > now)

    elif status == "Expired":
        query = query.filter(models.Post.expires_at <= now)

    db_posts = query.all()
    return [
        build_post_response(post)
        for post in db_posts
    ]