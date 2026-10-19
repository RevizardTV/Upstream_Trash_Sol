# tests/e2e/conftest.py
import os
import pytest
import redis

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