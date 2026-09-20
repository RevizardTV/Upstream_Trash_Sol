# tests/test_redis.py
import pytest
import anyio


@pytest.mark.anyio
async def test_redis_cache_set_and_get(mock_redis):
    """Verify basic key-value operations in Redis."""
    await mock_redis.set("user:1:otp", "123456")
    cached_val = await mock_redis.get("user:1:otp")

    # fakeredis with decode_responses=True returns str, otherwise bytes
    if isinstance(cached_val, bytes):
        cached_val = cached_val.decode("utf-8")

    assert cached_val == "123456"


@pytest.mark.anyio
async def test_redis_otp_ttl_expiration(mock_redis):
    """Verify OTP keys expire after their Time-To-Live (TTL)."""
    await mock_redis.setex("otp:9876543210", 1, "654321")  # 1 second TTL
    assert (await mock_redis.get("otp:9876543210")) is not None

    await anyio.sleep(1.1)  # Async sleep for expiration
    assert (await mock_redis.get("otp:9876543210")) is None


@pytest.mark.anyio
async def test_redis_rate_limiting_counter(mock_redis):
    """Verify Redis increments request counters for rate limiting."""
    key = "rate_limit:user:1"
    await mock_redis.incr(key)
    await mock_redis.incr(key)

    attempts = int(await mock_redis.get(key))
    assert attempts == 2