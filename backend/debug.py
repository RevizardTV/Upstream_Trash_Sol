from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from py_scripts.database import get_db, UserProfile, RecyclingEntry, StaffProfile
from py_scripts.config import config
from typing import Optional
router = APIRouter(prefix="/api/admin", tags=["Admin Debug"])

def verify_admin_access(x_admin_secret: Optional[str] = Header(None, alias="x-admin-secret")):
    """Security dependency ensuring admin actions are signed with server secret."""
    secret_key = getattr(config, "EM_RESET_KEY", None)
    
    if not secret_key or not x_admin_secret or x_admin_secret != secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Invalid administrative authorization token."
        )

@router.get("/show-profiles", dependencies=[Depends(verify_admin_access)])
async def show_profiles(db: Session = Depends(get_db)):
    profiles = db.query(UserProfile).all()
    data = [
        {
            "id": p.id,
            "email": p.email,
            "full_name": p.full_name,
            "phone_number": p.phone_number,
            "city": p.city,
            "postal_code": p.postal_code,
            "premise_type": p.premise_type,
            "household_size": p.household_size,
            "upi_id": p.upi_id,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in profiles
    ]
    return {"status": "success", "count": len(data), "profiles": data}

@router.get("/show-staff", dependencies=[Depends(verify_admin_access)])
async def show_staff_profiles(db: Session = Depends(get_db)):
    staff_members = db.query(StaffProfile).all()
    data = [
        {
            "id": s.id,
            "email": s.email,
            "full_name": s.full_name,
            "assigned_pincode": s.assigned_pincode,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in staff_members
    ]
    return {"status": "success", "count": len(data), "staff": data}

@router.get("/show-data", dependencies=[Depends(verify_admin_access)])
async def show_data(table: str = Query(...), db: Session = Depends(get_db)):
    table_lower = table.lower()
    
    if table_lower in ["profile", "profiles", "user_profiles"]:
        return await show_profiles(db)
        
    elif table_lower in ["staff", "staff_profiles", "staffs"]:
        return await show_staff_profiles(db)

    elif table_lower in ["trash", "recycling", "recycling_entries", "queued_trash"]:
        records = db.query(RecyclingEntry).all()
        data = [
            {
                "entry_id": r.entry_id,
                "user_id": r.user_id,
                "waste_category": r.waste_category,
                "weight_kg": float(r.weight_kg),
                "payout_amount": float(r.payout_amount),
                "status": getattr(r, "status", "pending"),
                "rejection_reason": getattr(r, "rejection_reason", None),
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
        return {"status": "success", "table": "recycling_entries", "count": len(data), "data": data}

    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown table parameter '{table}'. Supported: 'Profile', 'Staff', 'Trash'."
        )

@router.post("/wipe-database", dependencies=[Depends(verify_admin_access)])
async def wipe_database(db: Session = Depends(get_db)):
    try:
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        db.execute(text("DELETE FROM recycling_entries;"))
        db.execute(text("DELETE FROM user_profiles;"))
        db.execute(text("DELETE FROM staff_profiles;"))
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()
        return {"status": "success", "message": "All records purged safely."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))