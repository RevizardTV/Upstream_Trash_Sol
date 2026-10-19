from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.models import UserProfile
from backend.database import get_db
from backend.custom_logging import logger

router = APIRouter(prefix="/api/user", tags=["User Profile"])

@router.get("/profile")
async def get_user_profile(
    user_id: Optional[int] = Query(None), 
    email: Optional[str] = Query(None), 
    user_authenticated: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    if user_authenticated != "true":
        raise HTTPException(status_code=401, detail="Unauthorized session")

    if not user_id and not email:
        raise HTTPException(status_code=400, detail="Must provide user_id or email query parameter")
    
    query = db.query(UserProfile)
    user = query.filter(UserProfile.id == user_id).first() if user_id else query.filter(UserProfile.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "status": "success",
        "profile": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "city": user.city,
            "postal_code": user.postal_code,
            "premise_type": user.premise_type,
            "household_size": user.household_size,
            "upi_id": user.upi_id,
            "profile_complete": getattr(user, "profile_complete", False)
        }
    }