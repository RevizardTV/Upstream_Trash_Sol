from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.config import config
from backend.redis_client import redis_client
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["Admin Debug"])

def verify_admin_secret(
    x_secret_key: Optional[str] = Header(None, alias="x-secret-key"),
    x_admin_secret: Optional[str] = Header(None, alias="x-admin-secret")
):
    """Verifies the request automatically against the server config EM_RESET_KEY."""
    secret_key = getattr(config, "EM_RESET_KEY", None)
    provided_key = x_secret_key or x_admin_secret
    
    if not secret_key or not provided_key or provided_key != secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Invalid emergency reset key."
        )

@router.get("/inspect/{entity}", dependencies=[Depends(verify_admin_secret)])
async def inspect_entity(entity: str, db: Session = Depends(get_db)):
    table_map = {
        "users": "user_profiles",
        "staff": "staff_profiles",
        "recycling": "recycling_entries"
    }
    if entity not in table_map:
        raise HTTPException(status_code=400, detail="Invalid entity.")
    
    table_name = table_map[entity]
    result = db.execute(text(f"SELECT * FROM `{table_name}`"))
    return {"status": "success", "rows": [dict(row._mapping) for row in result]}

@router.post("/wipe-all-data", dependencies=[Depends(verify_admin_secret)])
async def wipe_all_data(db: Session = Depends(get_db)):
    db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    db.execute(text("TRUNCATE TABLE recycling_entries;"))
    db.execute(text("TRUNCATE TABLE user_profiles;"))
    db.execute(text("TRUNCATE TABLE staff_profiles;"))
    db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    db.commit()
    return {"status": "success", "message": "All database tables wiped successfully."}

@router.post("/reset-redis", dependencies=[Depends(verify_admin_secret)])
async def reset_redis():
    await redis_client.flushall()
    return {"status": "success", "message": "Redis database reset successfully."}