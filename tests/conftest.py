# tests/conftest.py
import os

os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")

import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from py_scripts.database import Base, get_db
from py_scripts.main import app
from tests.factories import TestSession

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Mock Redis client in all app modules using fakeredis."""
    fake_redis = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr("py_scripts.main.redis_client", fake_redis)
    monkeypatch.setattr("py_scripts.otp_service.redis_client", fake_redis, raising=False)
    monkeypatch.setattr("py_scripts.login.db", fake_redis, raising=False)
    return fake_redis


@pytest.fixture(scope="function")
def db_session():
    """Create fresh schema in SQLite and bind session to factory_boy."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    # Rebind the scoped_session registry to return the active test session instance
    TestSession.configure(bind=test_engine)
    TestSession.registry.set(session)

    try:
        yield session
    finally:
        session.close()
        TestSession.remove()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()