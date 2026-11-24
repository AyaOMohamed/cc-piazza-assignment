import models
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from security import get_current_user
from schemas.post import PostCreate, PostResponse, build_post_response
from schemas.reaction import ReactionCreate, ReactionCountsResponse
from schemas.comment import CommentCreate, CommentResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from constants import TopicName, Status
import clock

router = APIRouter()


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
        created_at=clock.get_current_time(),
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
    topic: TopicName | None = Query(default=None),
    status: Status | None = Query(default=None),
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
    now = clock.get_current_time()

    if status == Status.LIVE:
        query = query.filter(models.Post.expires_at > now)

    elif status == Status.EXPIRED:
        query = query.filter(models.Post.expires_at <= now)

    db_posts = query.all()
    return [
        build_post_response(post)
        for post in db_posts
    ]

@router.get("/{post_id}", response_model=PostResponse, status_code=200)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return build_post_response(post)

@router.put("/{post_id}/reaction", response_model=ReactionCountsResponse, status_code=200)
def set_or_replace_reaction(
    post_id: int,
    reaction: ReactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Fetch the post
    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check whether the post has expired
    if post.expires_at <= clock.get_current_time():
        raise HTTPException(status_code=409, detail="Cannot react to an expired post")

    # Prevent the author from reacting to their own post
    if post.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot react to your own post")

    
    # Find the requested reaction type
    reaction_type = db.query(models.ReactionType).filter(
        models.ReactionType.name == reaction.reaction.value
    ).first()

    if reaction_type is None:
        raise HTTPException(status_code=422, detail="Invalid reaction type")

    # Check if the current user already reacted to this post
    existing_reaction = db.query(models.Reaction).filter(
        models.Reaction.post_id == post_id,
        models.Reaction.user_id == current_user.id
    ).first()

    if existing_reaction is None:
        # Create a new reaction
        new_reaction = models.Reaction(
            post_id=post_id,
            user_id=current_user.id,
            type_id=reaction_type.id
        )
        db.add(new_reaction)

    else:
        # Replace the existing reaction
        existing_reaction.type_id = reaction_type.id

    try:
        db.commit()
        db.refresh(post)

    except Exception:
        db.rollback()
        raise

    post_response = build_post_response(post)

    return ReactionCountsResponse(
        like_count=post_response.like_count,
        dislike_count=post_response.dislike_count
    )

@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=201)
def add_comment(
    post_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Fetch the post
    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check whether the post has expired
    if post.expires_at <= clock.get_current_time():
        raise HTTPException(status_code=409, detail="Cannot comment on an expired post")

    # Create a new comment
    new_comment = models.Comment(
        post_id=post_id,
        user_id=current_user.id,
        body=comment.body,
        created_at=clock.get_current_time()
    )
    db.add(new_comment)

    try:
        db.commit()
        db.refresh(new_comment)

    except Exception:
        db.rollback()
        raise

    return new_comment