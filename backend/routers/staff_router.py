from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
import bcrypt
from backend.models import StaffProfile, UserProfile, RecyclingEntry
from backend.database import get_db
from backend.custom_logging import logger, log_auth_event
from backend.otp_service import extract_client_ip, process_otp_request
from backend.schemas import StaffRegisterSchema, StaffLoginSchema, EntryReviewSchema

router = APIRouter(tags=["Staff Management"])

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8')[:72], bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8')[:72], hashed_password.encode('utf-8'))

@router.post("/api/staff/register")
async def register_staff_account(data: StaffRegisterSchema, request: Request, db: Session = Depends(get_db)):
    client_ip = extract_client_ip(request)
    existing = db.query(StaffProfile).filter(StaffProfile.email == data.email).first()
    if existing:
        log_auth_event("STAFF_REGISTER", data.email, "FAILED", client_ip, "Duplicate email")
        raise HTTPException(status_code=400, detail="Staff account with this email already exists.")
    
    new_staff = StaffProfile(
        email=data.email,
        full_name=data.full_name,
        assigned_pincode=data.assigned_pincode,
        password_hash=hash_password(data.password)
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    
    log_auth_event("STAFF_REGISTER", data.email, "SUCCESS", client_ip, f"Assigned PIN: {data.assigned_pincode}")
    return {"status": "success", "message": "Staff registered successfully!", "staff_id": new_staff.id}

@router.post("/api/staff/login")
async def login_staff_account(data: StaffLoginSchema, request: Request, db: Session = Depends(get_db)):
    client_ip = extract_client_ip(request)
    staff = db.query(StaffProfile).filter(StaffProfile.email == data.email).first()
    
    if not staff or not verify_password(data.password, staff.password_hash):
        log_auth_event("STAFF_LOGIN", data.email, "FAILED", client_ip, "Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid staff credentials.")

    await process_otp_request(data.email, client_ip, email_type="staff")
    return {
        "status": "otp_required",
        "message": "Password verified. Please enter the OTP sent to your email.",
        "email": staff.email,
        "staff_id": staff.id,
        "assigned_pincode": staff.assigned_pincode
    }

@router.get("/api/admin/district-users")
async def get_district_users(
    staff_pincode: str = Query(...),
    search: Optional[str] = Query(None),
    exact_pincode: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    if len(staff_pincode) < 3:
        raise HTTPException(status_code=400, detail="Staff pincode must be at least 3 digits.")

    district_prefix = staff_pincode[:3]
    query = db.query(UserProfile).filter(
        UserProfile.postal_code.isnot(None),
        UserProfile.postal_code.like(f"{district_prefix}%"),
        UserProfile.profile_complete == False
    )

    if search:
        search_filter = f"%{search}%"
        query = query.filter((UserProfile.full_name.ilike(search_filter)) | (UserProfile.email.ilike(search_filter)))

    if exact_pincode:
        query = query.filter(UserProfile.postal_code == exact_pincode)

    profiles = query.all()
    return {
        "status": "success",
        "district_prefix": district_prefix,
        "count": len(profiles),
        "profiles": [{ "id": p.id, "full_name": p.full_name, "email": p.email, "postal_code": p.postal_code, "premise_type": p.premise_type, "upi_id": p.upi_id } for p in profiles]
    }

@router.get("/api/admin/user-pending-entries/{user_id}")
async def get_user_pending_entries(user_id: int, db: Session = Depends(get_db)):
    entries = db.query(RecyclingEntry).filter(RecyclingEntry.user_id == user_id, RecyclingEntry.status == "pending").all()
    return {
        "status": "success",
        "user_id": user_id,
        "count": len(entries),
        "entries": [{"entry_id": e.entry_id, "waste_category": e.waste_category, "weight_kg": float(e.weight_kg), "payout_amount": float(e.payout_amount)} for e in entries]
    }

@router.post("/api/staff/entries/{entry_id}/review")
async def review_recycling_entry(entry_id: int, data: EntryReviewSchema, db: Session = Depends(get_db)):
    entry = db.query(RecyclingEntry).filter(RecyclingEntry.entry_id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Recycling entry not found.")

    entry.status = "approved" if data.action == "approve" else "declined"
    if data.action == "decline":
        entry.rejection_reason = data.rejection_reason or "Declined by district officer"
        
    db.commit()
    return {"status": "success", "message": f"Entry #{entry_id} updated."}