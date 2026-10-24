# tests/conftest.py
import os
import pytest
import fakeredis.aioredis
from fastapi.testclient import TestClient

# 1. Force testing environment variables BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["EM_RESET_KEY"] = "test_secret_key"
os.environ["RESEND_API_KEY"] = "re_test_dummy_key"

from sqlalchemy.orm import sessionmaker

from backend.main import app
import backend.models  # Registers all models to Base.metadata[cite: 6]
from backend.models import Base
from backend.database import get_db, engine as app_engine
from tests.factories import TestSession

# 2. Bind factory_boy to the shared app_engine so everything targets the same in-memory DB
TestSession.configure(bind=app_engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Automatically create all tables on the shared app engine before each test and drop them after."""
    Base.metadata.create_all(bind=app_engine)
    yield
    Base.metadata.drop_all(bind=app_engine)


@pytest.fixture(scope="function")
def db_session(setup_database):
    """Provides an isolated database session for each test using the shared app engine."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


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