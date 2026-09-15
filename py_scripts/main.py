from hashlib import sha256
import json
import os
import sys
from typing import Optional
from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
import redis.asyncio as redis
from resend.exceptions import ResendError
import io

# Database Imports
from sqlalchemy.orm import Session
from py_scripts.database import Base, UserProfile, RecyclingEntry, StaffProfile, engine, get_db

# Debug Router & Core Utilities
from py_scripts.debug import router as debug_router
from py_scripts.config import config
from py_scripts.emailSend import send_email
import py_scripts.login as login
from pdf_generator import generate_receipt_pdf

# Logging Utilities
from py_scripts.logging import (
    PerformanceLoggingMiddleware, 
    log_auth_event, 
    log_recycling_action, 
    logger
)

# Ensure project directory is in PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Auto-create tables on startup
Base.metadata.create_all(bind=engine)

# Redis Connection Initialization
redis_url = os.getenv("REDIS_URL") or getattr(config, "REDIS_URL", None)
if not redis_url:
    logger.critical("CRITICAL ERROR: REDIS_URL environment variable is missing!")
    sys.exit(1)

redis_client = redis.from_url(redis_url, decode_responses=True)

# Application Initialization
app = FastAPI(title="EcoRecycle API")

# Register Performance & Route Timing Middleware
app.add_middleware(PerformanceLoggingMiddleware)

# CORS Middleware Configuration
origins = [
    "https://upstream-trash-sol.onrender.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Debug Router
app.include_router(debug_router)

# Mount Static File Directories
for folder in ["static", "image_assets", "webpages"]:
    os.makedirs(folder, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Pydantic Schemas ---

class OTPRequest(BaseModel):
    email_address: EmailStr

class OTPVerify(BaseModel):
    email_address: EmailStr
    otp_code: str

class ProfileCreateSchema(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: str
    city: str
    postal_code: str
    premise_type: str = "house"
    household_size: int = 1
    upi_id: Optional[str] = None

class RecyclingEntrySchema(BaseModel):
    user_id: int
    waste_category: str
    weight_kg: float
    payout_amount: float

    class Config:
        from_attributes = True

class StaffRegisterSchema(BaseModel):
    email: EmailStr
    full_name: str
    assigned_pincode: str
    password: str

class StaffLoginSchema(BaseModel):
    email: EmailStr
    password: str

class StaffReviewSchema(BaseModel):
    action: str  # "approve" or "decline"
    rejection_reason: Optional[str] = None

class EntryReviewSchema(BaseModel):
    action: str  # "approve" or "decline"
    rejection_reason: Optional[str] = None
    staff_id: Optional[int] = None


# --- Frontend Webpage Handlers ---

@app.get("/")
async def serve_home():
    return FileResponse("webpages/index.html")

@app.get("/login")
async def serve_login():
    return FileResponse("webpages/login.html")

@app.get("/payment")
async def serve_payment(session_authenticated: Optional[str] = Cookie(None)):
    if session_authenticated != "true":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/payment.html")

@app.get("/register-payment")
async def serve_register_payment():
    return FileResponse("webpages/register_payment.html")

@app.get("/pending-payments")
async def serve_pending_payments():
    return FileResponse("webpages/pending_payments.html")

@app.get("/reviewed-requests")
async def serve_reviewed_requests():
    return FileResponse("webpages/reviewed_requests.html")

@app.get("/payment-info")
async def serve_payment_info():
    return FileResponse("webpages/payment_info.html")

@app.get("/register-profile")
async def serve_profile_registration():
    return FileResponse("webpages/register_profile.html")

@app.get("/register-staff")
async def serve_register_staff():
    return FileResponse("webpages/register_staff.html")

@app.get("/staff-login")
async def serve_staff_login():
    return FileResponse("webpages/staff_login.html")

@app.get("/staff-dashboard")
async def serve_staff_dashboard(
    session_authenticated: Optional[str] = Cookie(None),
    staff_authenticated: Optional[str] = Cookie(None)
):
    if session_authenticated != "true" and staff_authenticated != "true":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/staff_dashboard.html")

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session_authenticated", path="/")
    response.delete_cookie(key="staff_authenticated", path="/")
    return response


# --- User Authentication Endpoints ---

@app.post("/api/auth/request-otp")
async def request_otp(data: OTPRequest, request: Request):
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"
    
    otp, error = await login.generate_otp(data.email_address, client_ip)
    
    if error or not otp:
        log_auth_event("OTP_REQUEST", data.email_address, "FAILED", client_ip, error or "Rate limit exceeded")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail=error or "Failed to generate OTP code."
        )
    
    try:
        await send_email(
            to_email=data.email_address,
            subject="EcoRecycle - Your Login OTP",
            body=otp
        )
        log_auth_event("OTP_REQUEST", data.email_address, "SUCCESS", client_ip, "OTP sent via email")
        return {"status": "success", "message": "OTP code dispatched successfully"}
        
    except ResendError as re_err:
        log_auth_event("OTP_REQUEST", data.email_address, "ERROR", client_ip, f"Resend API Error: {str(re_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resend Mail Error: {str(re_err)}"
        )
    except Exception as e:
        log_auth_event("OTP_REQUEST", data.email_address, "ERROR", client_ip, f"Mail delivery error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="OTP saved to database, but email delivery service failed."
        )

@app.post("/api/auth/verify-otp")
async def verify_otp_route(data: OTPVerify, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        is_valid, error = await login.verify_otp(data.email_address, data.otp_code)
        
        if not is_valid:
            log_auth_event("OTP_VERIFY", data.email_address, "FAILED", client_ip, error or "Invalid code")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=error or "Invalid or expired verification code."
            )
            
        log_auth_event("OTP_VERIFY", data.email_address, "SUCCESS", client_ip, "Session cookie granted")
        response = JSONResponse(
            content={"status": "success", "message": "OTP verified successfully."}
        )
        response.set_cookie(
            key="session_authenticated",
            value="true",
            httponly=False,
            samesite="lax",
            path="/"
        )
        return response
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"OTP Verification system failure for {data.email_address}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying the OTP."
        )

@app.post("/api/auth/complete-profile")
async def save_user_profile(data: ProfileCreateSchema, response: Response, db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.email == data.email).first()
    
    user_data = data.model_dump()
    user_data["profile_complete"] = False  # Mark unreviewed by default

    if not user:
        user = UserProfile(**user_data)
        db.add(user)
        logger.info(f"Created new user profile for {data.email}")
    else:
        for field, value in user_data.items():
            setattr(user, field, value)
        logger.info(f"Updated existing user profile for User ID #{user.id}")
            
    db.commit()
    db.refresh(user)

    response.set_cookie(
        key="session_authenticated",
        value="true",
        httponly=False,
        samesite="lax",
        path="/"
    )
    return {"status": "success", "message": "Profile saved successfully!", "user_id": user.id}


# --- User Profile & Data Endpoints ---

@app.get("/api/user/profile")
async def get_user_profile(user_id: int = Query(None), email: str = Query(None), db: Session = Depends(get_db)):
    if not user_id and not email:
        raise HTTPException(status_code=400, detail="Must provide user_id or email query parameter")
    
    query = db.query(UserProfile)
    if user_id:
        user = query.filter(UserProfile.id == user_id).first()
    else:
        user = query.filter(UserProfile.email == email).first()

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


# --- Staff Authorization Endpoints ---

@app.post("/api/staff/register")
async def register_staff_account(data: StaffRegisterSchema, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    existing = db.query(StaffProfile).filter(StaffProfile.email == data.email).first()
    if existing:
        log_auth_event("STAFF_REGISTER", data.email, "FAILED", client_ip, "Duplicate email")
        raise HTTPException(status_code=400, detail="Staff account with this email already exists.")
    
    hashed_password = sha256(data.password.encode()).hexdigest()
    new_staff = StaffProfile(
        email=data.email,
        full_name=data.full_name,
        assigned_pincode=data.assigned_pincode,
        password_hash=hashed_password
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    
    log_auth_event("STAFF_REGISTER", data.email, "SUCCESS", client_ip, f"Assigned PIN: {data.assigned_pincode}")
    return {"status": "success", "message": "Staff registered successfully!", "staff_id": new_staff.id}

@app.post("/api/staff/login")
async def login_staff_account(data: StaffLoginSchema, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    hashed_password = sha256(data.password.encode()).hexdigest()
    
    staff = db.query(StaffProfile).filter(
        StaffProfile.email == data.email, 
        StaffProfile.password_hash == hashed_password
    ).first()
    
    if not staff:
        log_auth_event("STAFF_LOGIN", data.email, "FAILED", client_ip, "Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid staff credentials.")
        
    log_auth_event("STAFF_LOGIN", data.email, "SUCCESS", client_ip, f"Staff ID: {staff.id}")
    
    response = JSONResponse(content={
        "status": "success", 
        "staff_id": staff.id, 
        "email": staff.email, 
        "assigned_pincode": staff.assigned_pincode
    })
    response.set_cookie(key="staff_authenticated", value="true", httponly=False, samesite="lax", path="/")
    response.set_cookie(key="session_authenticated", value="true", httponly=False, samesite="lax", path="/")
    return response

@app.post("/api/staff/users/{user_id}/review")
async def review_user_profile(
    user_id: int, 
    data: StaffReviewSchema, 
    db: Session = Depends(get_db)
):
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User ID #{user_id} not found.")

    user.profile_complete = True if data.action == "approve" else False
    db.commit()
    return {"status": "success", "message": f"User profile status updated to {data.action}"}


# --- Recycling & Waste Transactions ---

@app.post("/api/recycling/entry")
async def add_recycling_entry(data: RecyclingEntrySchema, db: Session = Depends(get_db)):
    try:
        user = db.query(UserProfile).filter(UserProfile.id == data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {data.user_id} not found in user_profiles.")
            
        new_entry = RecyclingEntry(
            user_id=data.user_id,
            waste_category=data.waste_category,
            weight_kg=data.weight_kg,
            payout_amount=data.payout_amount,
            status="pending"
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        
        log_recycling_action("SUBMIT", data.user_id, data.weight_kg, "PENDING", f"Category: {data.waste_category}")
        return {
            "status": "success", 
            "message": "Recycling transaction recorded!", 
            "entry_id": new_entry.entry_id
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save recycling entry for User ID #{data.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database insertion failed: {str(e)}")

@app.get("/api/recycling/pending-payments")
async def get_pending_payments(
    user_id: int = Query(None), 
    email: str = Query(None), 
    db: Session = Depends(get_db)
):
    if not user_id and not email:
        raise HTTPException(status_code=400, detail="Must provide user_id or email")
    
    if not user_id and email:
        user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found")
        user_id = user.id

    entries = db.query(RecyclingEntry).filter(
        RecyclingEntry.user_id == user_id,
        RecyclingEntry.status == "pending"
    ).order_by(RecyclingEntry.entry_id.desc()).all()
    
    total_payout = sum(float(entry.payout_amount) for entry in entries)

    return {
        "status": "success",
        "user_id": user_id,
        "total_pending_amount": total_payout,
        "count": len(entries),
        "entries": [
            {
                "entry_id": entry.entry_id,
                "waste_category": entry.waste_category,
                "weight_kg": float(entry.weight_kg),
                "payout_amount": float(entry.payout_amount),
                "created_at": entry.created_at.isoformat() if getattr(entry, "created_at", None) else None
            }
            for entry in entries
        ]
    }

@app.get("/api/recycling/reviewed-requests")
async def get_reviewed_requests(
    user_id: int = Query(None), 
    email: str = Query(None), 
    db: Session = Depends(get_db)
):
    if not user_id and not email:
        raise HTTPException(status_code=400, detail="Must provide user_id or email")
    
    if not user_id and email:
        user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found")
        user_id = user.id

    entries = db.query(RecyclingEntry).filter(
        RecyclingEntry.user_id == user_id,
        RecyclingEntry.status.in_(["approved", "declined"])
    ).order_by(RecyclingEntry.entry_id.desc()).all()

    total_approved = sum(float(e.payout_amount) for e in entries if getattr(e, "status", None) == "approved")

    return {
        "status": "success",
        "user_id": user_id,
        "total_approved_earnings": total_approved,
        "count": len(entries),
        "entries": [
            {
                "entry_id": e.entry_id,
                "waste_category": e.waste_category,
                "weight_kg": float(e.weight_kg),
                "payout_amount": float(e.payout_amount),
                "status": getattr(e, "status", "approved"),
                "rejection_reason": getattr(e, "rejection_reason", None),
                "created_at": e.created_at.isoformat() if getattr(e, "created_at", None) else None
            }
            for e in entries
        ]
    }

@app.get("/api/recycling/summary")
async def get_user_recycling_summary(
    user_id: int = Query(None), 
    email: str = Query(None), 
    db: Session = Depends(get_db)
):
    if not user_id and email:
        user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user.id

    entries = db.query(RecyclingEntry).filter(RecyclingEntry.user_id == user_id).all()

    # Total Earnings only includes approved entries
    approved_total = sum(float(e.payout_amount) for e in entries if getattr(e, "status", "pending") == "approved")
    pending_total = sum(float(e.payout_amount) for e in entries if getattr(e, "status", "pending") == "pending")
    total_approved_weight = sum(float(e.weight_kg) for e in entries if getattr(e, "status", "pending") == "approved")

    return {
        "status": "success",
        "total_earnings": approved_total,
        "pending_release": pending_total,
        "eco_credits": int(total_approved_weight * 10),
        "entries": [
            {
                "entry_id": e.entry_id,
                "waste_category": e.waste_category,
                "weight_kg": float(e.weight_kg),
                "payout_amount": float(e.payout_amount),
                "status": getattr(e, "status", "pending"),
                "rejection_reason": getattr(e, "rejection_reason", None),
                "created_at": e.created_at.isoformat() if getattr(e, "created_at", None) else None
            }
            for e in entries
        ]
    }


# --- Staff District Inspection API ---

@app.get("/api/admin/district-users")
async def get_district_users(
    staff_pincode: str = Query(...),
    search: str = Query(None),
    exact_pincode: str = Query(None),
    db: Session = Depends(get_db)
):
    if len(staff_pincode) < 3:
        raise HTTPException(status_code=400, detail="Staff pincode must be at least 3 digits.")

    district_prefix = staff_pincode[:3]
    
    # Exclude already completed/approved users
    query = db.query(UserProfile).filter(
        UserProfile.postal_code.like(f"{district_prefix}%"),
        UserProfile.profile_complete == False
    )

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (UserProfile.full_name.ilike(search_filter)) | 
            (UserProfile.email.ilike(search_filter))
        )

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


# --- Admin Utility Endpoint ---

@app.get("/api/admin/show-data")
async def show_data(table: str = Query(...), db: Session = Depends(get_db)):
    table_lower = table.lower()
    
    if table_lower in ["profile", "profiles", "user_profiles"]:
        records = db.query(UserProfile).all()
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
                "profile_complete": getattr(p, "profile_complete", False),
                "created_at": p.created_at.isoformat() if getattr(p, "created_at", None) else None
            }
            for p in records
        ]
        return {"status": "success", "table": "user_profiles", "count": len(data), "data": data}

    elif table_lower in ["trash", "recycling", "recycling_entries", "queued_trash"]:
        records = db.query(RecyclingEntry).all()
        data = [
            {
                "entry_id": r.entry_id,
                "user_id": r.user_id,
                "waste_category": r.waste_category,
                "weight_kg": r.weight_kg,
                "payout_amount": r.payout_amount,
                "status": getattr(r, "status", "pending")
            }
            for r in records
        ]
        return {"status": "success", "table": "recycling_entries", "count": len(data), "data": data}

    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown table parameter '{table}'."
        )
        
# --- GET Household Pending Trash Entries for Staff Review ---
@app.get("/api/admin/user-pending-entries/{user_id}")
async def get_user_pending_entries(user_id: int, db: Session = Depends(get_db)):
    entries = db.query(RecyclingEntry).filter(
        RecyclingEntry.user_id == user_id,
        RecyclingEntry.status == "pending"
    ).all()
    
    return {
        "status": "success",
        "user_id": user_id,
        "count": len(entries),
        "entries": [
            {
                "entry_id": e.entry_id,
                "waste_category": e.waste_category,
                "weight_kg": float(e.weight_kg),
                "payout_amount": float(e.payout_amount),
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in entries
        ]
    }

@app.get("/api/recycling/receipt/{entry_id}")
async def download_receipt(entry_id: int):
    mock_entry = {
        "entry_id": entry_id,
        "waste_category": "plastic",
        "weight_kg": 12.5,
        "payout_amount": 150.00,
        "status": "approved",
        "station_id": "BIN-COIMBATORE-08",
        "created_at": "2026-03-28",
        "user_name": "Jane Doe"
    }

    if not mock_entry:
        raise HTTPException(status_code=404, detail="Recycling entry not found.")

    pdf_bytes = generate_receipt_pdf(mock_entry)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=receipt_entry_{entry_id}.pdf"
        }
    )

# --- REVIEW (Approve / Decline) Waste Entry ---
@app.post("/api/staff/entries/{entry_id}/review")
async def review_recycling_entry(
    entry_id: int, 
    data: EntryReviewSchema, 
    db: Session = Depends(get_db)
):
    entry = db.query(RecyclingEntry).filter(RecyclingEntry.entry_id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Recycling entry not found.")

    new_status = "approved" if data.action == "approve" else "declined"
    
    entry.status = new_status
    entry.reviewed_by_staff_id = data.staff_id
    if data.action == "decline":
        entry.rejection_reason = data.rejection_reason or "Declined by district officer"
        
    db.commit()
    db.refresh(entry)
    
    return {"status": "success", "message": f"Entry #{entry_id} successfully updated to {new_status}."}