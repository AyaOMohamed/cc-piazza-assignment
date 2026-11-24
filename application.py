from fastapi import FastAPI

import models
from database import engine, SessionLocal
from routers import auth, posts, topics
from seeds.seed import seed_database


def create_app(db_engine=engine, session_factory=SessionLocal):
    models.Base.metadata.create_all(bind=db_engine)

    with session_factory() as db:
        seed_database(db)

    app = FastAPI()

    app.include_router(auth.router, prefix="/auth")
    app.include_router(posts.router, prefix="/posts")
    app.include_router(topics.router, prefix="/topics")

    @app.get("/health")
    def home():
        return {"message": "Welcome to Piazza!"}

    return app
