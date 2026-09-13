from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from py_scripts.database import get_db, UserProfile, RecyclingEntry, StaffProfile

router = APIRouter(prefix="/api/admin", tags=["Admin Debug"])

@router.get("/show-profiles")
async def show_profiles(db: Session = Depends(get_db)):
    """Fetch all registered user profiles."""
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

@router.get("/show-staff")
async def show_staff_profiles(db: Session = Depends(get_db)):
    """Extract and display all registered staff profiles."""
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

@router.get("/show-data")
async def show_data(table: str = Query(...), db: Session = Depends(get_db)):
    """Inspect tables dynamically (Profile, Staff, Trash/Recycling)."""
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

@router.post("/wipe-database")
async def wipe_database(db: Session = Depends(get_db)):
    """Purge entries across profiles, staff, and recycling queues."""
    try:
        # Disable foreign key checks for clean truncation across tables
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        db.execute(text("TRUNCATE TABLE recycling_entries;"))
        db.execute(text("TRUNCATE TABLE user_profiles;"))
        db.execute(text("TRUNCATE TABLE staff_profiles;"))
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()
        return {"status": "success", "message": "All user profiles, staff records, and recycling entries purged."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to wipe database: {str(e)}"
        )
        
@router.get("/district-users")
async def get_district_users(
    staff_pincode: str = Query(...),
    search: str = Query(None), # Optional search term for name or email
    exact_pincode: str = Query(None), # Optional filter for exact 6-digit PIN
    db: Session = Depends(get_db)
):
    """
    Fetch all users within the staff member's sorting district (matching first 3 digits of PIN).
    Allows searching by user name, email, or exact locality pincode.
    """
    if len(staff_pincode) < 3:
        raise HTTPException(status_code=400, detail="Staff pincode must be at least 3 digits.")

    district_prefix = staff_pincode[:3]
    query = db.query(UserProfile).filter(UserProfile.postal_code.like(f"{district_prefix}%"))

    # Apply search filter if provided (matches user name or email)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (UserProfile.full_name.ilike(search_filter)) | 
            (UserProfile.email.ilike(search_filter))
        )

    # Apply exact pincode filter if provided
    if exact_pincode:
        query = query.filter(UserProfile.postal_code == exact_pincode)

    profiles = query.all()

    return {
        "status": "success",
        "district_prefix": district_prefix,
        "count": len(profiles),
        "profiles": [
            {
                "id": p.id,
                "full_name": p.full_name,
                "email": p.email,
                "phone_number": p.phone_number,
                "city": p.city,
                "postal_code": p.postal_code,
                "premise_type": p.premise_type,
                "household_size": p.household_size,
                "upi_id": p.upi_id
            } for p in profiles
        ]
    }