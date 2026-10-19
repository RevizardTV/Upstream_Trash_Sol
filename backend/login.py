import secrets
import redis.asyncio as redis
from redis.asyncio import Redis
from typing import cast, Any
import logging
from backend.config import config

logger = logging.getLogger(__name__)

redis_url = config.REDIS_URL
if not redis_url:
    raise ValueError("REDIS URL env var is not set")
db: Redis = redis.from_url(redis_url, decode_responses=True)

EXPIRY = 60       # OTP codes last 1 minute (60 seconds)
MAX_ATTEMPTS = 3   # Maximum allowed attempts

async def generate_otp(email: str, ip: str):
    """Generates and saves an OTP, returns the code."""
    if not email:
        return None, "email Address payload is missing or invalid."
    
    clean_email = email.lower().strip()
    
    if not ip or ip == "127.0.0.1":
        ip = "dev_fallback_track" 
    
    if await db.exists(f"cooldown:{clean_email}"):
        return None, "Please wait 60 seconds."
    
    otp = "".join(secrets.choice("0123456789") for _ in range(6))
    
    pipe = db.pipeline()
    pipe.hset(clean_email, mapping={"otp": otp, "attempts": 0})
    pipe.expire(clean_email, EXPIRY)
    pipe.setex(f"cooldown:{clean_email}", 60, "active")
    pipe.incr(f"ip_rate:{ip}")
    pipe.expire(f"ip_rate:{ip}", 3600, nx=True)
    
    results = await pipe.execute()
    if not results or len(results) < 2:
        return None, "Database transactional failure"
    
    return otp, None


async def verify_otp(email: str, code: str):
    """Verifies the OTP strictly against Redis records."""
    clean_email = email.lower().strip()
    session = await cast(Any, db.hgetall(clean_email))
    
    if not session:
        return False, "Code expired or invalid"
        
    otp_in_redis = session.get("otp")
    if not otp_in_redis:
        return False, "Code expired or invalid"

    if not secrets.compare_digest(otp_in_redis, code):
        try:
            new_attempts = await db.hincrby(clean_email, "attempts", 1)
            new_attempts = int(new_attempts)
            if new_attempts >= MAX_ATTEMPTS:
                await db.delete(clean_email)
                return False, "Session locked due to too many attempts."
            return False, f"Invalid code. {MAX_ATTEMPTS - new_attempts} attempts remaining."
        except Exception as e:
            logger.error(f"Error updating wrong attempt security counter: {e}")
            return False, "Error updating wrong attempt security counter."
        
    await db.delete(clean_email)
    return True, None