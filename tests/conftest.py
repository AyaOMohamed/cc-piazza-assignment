import os

# test-only secret
os.environ["JWT_SECRET"] = "test-only-secret-not-for-deployment-123456789"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application import create_app
from database import get_db
from datetime import datetime
from unittest.mock import patch

import clock


@pytest.fixture
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'piazza-test.db'}",
        connect_args={"check_same_thread": False},
    )
    sessions = sessionmaker(bind=engine)

    app = create_app(db_engine=engine, session_factory=sessions)

    def override_db():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture
def mock_clock():
    current_time = [datetime(2026, 1, 1, 12, 0, 0)]

    with patch.object(
        clock,
        "get_current_time",
        side_effect=lambda: current_time[0],
    ):
        yield current_time
