# tests/e2e/conftest.py
import os
import pytest
import redis
import httpx
from tests.e2e.utils import verify_mailpit_health
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