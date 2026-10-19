# tests/e2e/conftest.py
import os
import pytest
import redis
import httpx
from tests.e2e.utils import verify_mailpit_health
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.models import Base, UserProfile
def pytest_configure(config):
    """Set test environment variables programmatically for the pytest session."""
    os.environ["USE_MAILPIT"] = "true"
    os.environ["SMTP_HOST"] = "localhost"
    os.environ["SMTP_PORT"] = "1025"
    os.environ["ENVIRONMENT"] = "test"
    print("⚙️ [PYTEST SETUP] Test environment variables loaded successfully.")

@pytest.fixture(scope="function", autouse=True)
def flush_docker_redis_for_e2e():
    """Synchronously flushes Docker Redis before each E2E test to clear rate limits."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Use synchronous Redis client to avoid coroutine overhead in sync fixtures
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    try:
        client.flushall()
    except Exception as e:
        print(f"Docker Redis flush skipped or failed (Is Docker running?): {e}")
    finally:
        client.close()
        
@pytest.fixture(scope="session", autouse=True)
def verify_backend_health():
    """Ensures FastAPI backend is running before executing E2E tests."""
    url = "http://localhost:8000/docs" # or a health check endpoint
    try:
        response = httpx.get(url, timeout=3.0)
        print("✅ Backend is online.")
    except Exception:
        raise RuntimeError("❌ FastAPI backend is NOT running on http://localhost:8000! Start it using uvicorn.")
        
@pytest.fixture(autouse=True)
def mailpit_smoke_test():
    """Runs a smoke check on Mailpit before each test execution."""
    verify_mailpit_health()

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Ensure all database tables are created at the start of the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    # Optional cleanup if needed after the full test session

@pytest.fixture
def db_session():
    """Provide a fresh database session for a test and close it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def seed_test_user(db_session: Session):
    """Automatically seed the test user with all required non-nullable fields."""
    test_email = "delivered@resend.dev"
    existing_user = db_session.query(UserProfile).filter(UserProfile.email == test_email).first()

    if not existing_user:
        new_user = UserProfile(
            email=test_email,
            full_name="Test User",
            phone_number="9876543210",
            city="Coimbatore",
            postal_code="641001",
            premise_type="house",
            household_size=1,
            profile_complete=True
        )
        db_session.add(new_user)
        db_session.commit()
    else:
        # Patch any missing mandatory fields on an existing record
        updated = False
        if not existing_user.phone_number:
            existing_user.phone_number = "9876543210"
            updated = True
        if not existing_user.city:
            existing_user.city = "Coimbatore"
            updated = True
        if not existing_user.postal_code:
            existing_user.postal_code = "641001"
            updated = True

        if updated:
            db_session.commit()