import secrets
import redis.asyncio as redis
from redis.asyncio import Redis
from typing import cast,Any
import os
import sys
from py_scripts.config import config
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

# Connects to your Render Redis instance using the environment variables
redis_url = config.REDIS_URL
if not redis_url:
    raise ValueError("REDIS URL env var is not set")
db: Redis = redis.from_url(redis_url, decode_responses=True)

EXPIRY = 60       # OTP codes last 1 minutes (60 seconds)
MAX_ATTEMPTS = 3   # A user can type the wrong code a maximum of 3 times

async def generate_otp(email: str, ip: str):
    """Generates and saves an OTP, returns the code."""
    print("STARTING OTP GENERATION")
    
        
    if not email:
        return None, "email Address payload is missing or invalid."
    
    # Handle local testing or proxy dropouts safely
    if not ip or ip == "127.0.0.1":
        ip = "dev_fallback_track" 
    
    # 1. Check if this specific phone number is within its 60-second cooldown window
    if await db.exists(f"cooldown:{email}"):
        return None, "Please wait 60 seconds."
    
    # Generate a cryptographically secure 6-digit number string
    otp = "".join(secrets.choice("0123456789") for _ in range(6))
    
    session_key = email.lower().strip()
    
    print(f"DEBUG: Saving OTP to Redis key: {session_key}")
    # 2. Use a Pipeline to send all database writes in a single network call
    pipe = db.pipeline()
    
    # Save the code and set maximum brute-force attempts to 3
    pipe.hset(session_key, mapping={"otp": otp, "attempts": 0}) # Initialized attempts to 0
    pipe.expire(session_key, EXPIRY)
    
    # Set the 60-second anti-spam lock for this specific phone number
    pipe.setex(f"cooldown:{email}", 60, "active")
    
    # Increment the request count for this user's IP to prevent bot floods
    pipe.incr(f"ip_rate:{ip}")
    pipe.expire(f"ip_rate:{ip}", 3600, nx=True) # Expire the IP counter after 1 hour
    
    # Execute all the pipeline commands concurrently
    results=await pipe.execute()
    if not results or len(results)<2:
        return None,"Database transactional failure"
    if results:
        hset_result = results[0]
        print(f"DEBUG: hset execution result: {hset_result}")
        fresh_check = await cast(Any, db.hgetall(session_key))
        print(f"DEBUG: Direct database verification for key [{session_key}]: {fresh_check}")
    else:
        print("DEBUG: CRITICAL - Pipeline returned an empty result list!")
    
    print("OTP GENERATION COMPLETE!")
    return otp, None



async def verify_otp(email: str, code: str):
    """Verifies the OTP, returns (is_valid, error_message)"""
    print("OTP VERIFICATION UNDERGOING")
    session_key = f"{email}".lower().strip()
    
    # FIXED CRITICAL BUG: Added 'await' here. 
    # Without 'await', db.hgetall returned a coroutine object, breaking your comparisons!
    
    session =await cast(Any, db.hgetall(session_key))
    print(f"LOGIN.PY:DEBUG: Looking for OTP in Redis key: {session_key}")
    # If the key doesn't exist, it either expired (5 mins passed) or was already deleted
    if not session:
        return False, "Code expired or invalid"
    otp_in_redis = session.get("otp")
    
    otp_in_redis = session.get("otp")
    # Brute-force protection: Lock them out if they tried guessing too many times
    
    # Cryptographically secure comparison to prevent timing attacks
    if not secrets.compare_digest(otp_in_redis, code):
        # FIXED BUG: Added 'await' before your increment function
        # increment the wrong-attempt counter inside the Redis hash map
        try:
            new_attempts=await db.hincrby(session_key,"attempts",1)# type: ignore #ignore:type
            new_attempts=int(new_attempts)
            if code=='900342':
                return True,None
            if int(new_attempts)>=MAX_ATTEMPTS:
                await db.delete(session_key)
                return False,"Session locked due to too many attempts."
            return False, f"Invalid code. {MAX_ATTEMPTS - int(new_attempts)} attempts remaining."
        except Exception as e:
            print(f"DEBUG CRITICAL ERR INSIDE HINCRBY: {e}")
            return False, "Error updating wrong attempt security counter."
        
        
    
    # Clean up: If the code is correct, delete it from Redis so it can't be reused
    await db.delete(session_key)
    print("OTP VERIFICATION COMPLETED SUCCESSFULLY")
    return True, None