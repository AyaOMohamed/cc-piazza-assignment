from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    DateTime,
    CheckConstraint,
    Table,
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    posts = relationship("Post", back_populates="user")


post_topics = Table(
    "post_topics",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
)


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    posts = relationship("Post", secondary=post_topics, back_populates="topics")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    topics = relationship("Topic", secondary=post_topics, back_populates="posts")
    user = relationship("User", back_populates="posts")
    reactions = relationship("Reaction", back_populates="post")
    comments = relationship("Comment", back_populates="post")

    __table_args__ = (
        CheckConstraint(
            "expires_at > created_at", name="ck_post_expire_after_creation"
        ),
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)

    post = relationship("Post", back_populates="comments")


class ReactionType(Base):
    __tablename__ = "reaction_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    reactions = relationship("Reaction", back_populates="reaction_type")


class Reaction(Base):
    __tablename__ = "reactions"

    type_id = Column(
        Integer, ForeignKey("reaction_types.id"), primary_key=True, nullable=False
    )
    post_id = Column(
        Integer, ForeignKey("posts.id"), primary_key=True, nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, nullable=False)

    post = relationship("Post", back_populates="reactions")
    reaction_type = relationship("ReactionType", back_populates="reactions")
