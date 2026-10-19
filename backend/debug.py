from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.models import Base
from backend.config import config
from backend.redis_client import redis_client
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["Admin Debug"])

def verify_admin_secret(
    x_secret_key: Optional[str] = Header(None, alias="x-secret-key"),
    x_admin_secret: Optional[str] = Header(None, alias="x-admin-secret")
):
    """Security dependency supporting both x-secret-key and x-admin-secret headers."""
    secret_key = getattr(config, "EM_RESET_KEY", None)
    provided_key = x_secret_key or x_admin_secret
    
    if not secret_key or not provided_key or provided_key != secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Invalid administrative authorization token."
        )

@router.get("/redis-inspect", dependencies=[Depends(verify_admin_secret)])
async def redis_inspect():
    try:
        keys = await redis_client.keys("*")
        records = []
        for k in keys:
            ttl = await redis_client.ttl(k)
            val = await redis_client.get(k)
            if val is None:
                val = str(await redis_client.type(k))
            records.append({"key": k, "ttl_seconds": ttl, "value": val})
        return {"status": "success", "records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-reset", dependencies=[Depends(verify_admin_secret)])
async def emergency_reset():
    try:
        await redis_client.flushall()
        return {"status": "success", "message": "Redis database flushed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))