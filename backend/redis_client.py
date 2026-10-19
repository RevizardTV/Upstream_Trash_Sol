import os
import redis.asyncio as redis
from backend.config import config
from backend.custom_logging import logger
import sys

redis_url = os.getenv("REDIS_URL") or getattr(config, "REDIS_URL", None)
if not redis_url:
    logger.critical("CRITICAL ERROR: REDIS_URL environment variable is missing!")
    sys.exit(1)

redis_client = redis.from_url(redis_url, decode_responses=True)