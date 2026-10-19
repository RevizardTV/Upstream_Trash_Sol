# tests/conftest.py
import os
import pytest
import fakeredis.aioredis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Set Testing Environment Variables
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["EM_RESET_KEY"] = "test_secret_key"
os.environ["RESEND_API_KEY"] = "re_test_dummy_key"

from backend.main import app
from backend.models import Base
from backend.database import get_db
from tests.factories import TestSession

# 2. In-Memory SQLite Database for Fast Testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configure factory_boy session globally to bind to the engine
TestSession.configure(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides an isolated in-memory database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a FastAPI TestClient with the database dependency overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def mock_redis():
    """Provides a fake asynchronous Redis instance using fakeredis for unit tests."""
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield fake_redis
    await fake_redis.aclose()