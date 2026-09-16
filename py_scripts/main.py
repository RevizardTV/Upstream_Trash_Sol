import json
import os
import sys
import io
import traceback
import bcrypt
from typing import Optional

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, EmailStr
import redis.asyncio as redis

# Database Imports
from sqlalchemy.orm import Session
from py_scripts.database import Base, UserProfile, RecyclingEntry, StaffProfile, engine, get_db

# Debug Router & Core Utilities
from py_scripts.debug import router as debug_router
from py_scripts.config import config
from pdf_generator import generate_receipt_pdf

# OTP Modularized Import
from py_scripts.otp_service import (
    OTPRequest, 
    OTPVerify, 
    extract_client_ip, 
    process_otp_request, 
    process_otp_verification
)

# Logging Utilities
from py_scripts.logging import (
    PerformanceLoggingMiddleware, 
    log_auth_event, 
    log_recycling_action, 
    logger
)

# Direct Bcrypt Hashing (Bypasses Passlib 4.x Bugs)
def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
Base.metadata.create_all(bind=engine)

redis_url = os.getenv("REDIS_URL") or getattr(config, "REDIS_URL", None)
if not redis_url:
    logger.critical("CRITICAL ERROR: REDIS_URL environment variable is missing!")
    sys.exit(1)

redis_client = redis.from_url(redis_url, decode_responses=True)

app = FastAPI(title="EcoRecycle API")
app.add_middleware(PerformanceLoggingMiddleware)

# --- Middleware for Deep Payload and Request Inspection ---
# --- Global Middleware for Route Scope Cookie Enforcement ---
@app.middleware("http")
async def enforce_strict_route_cookie_scopes(request: Request, call_next):
    path = request.url.path
    response = await call_next(request)

    # Allow static assets and API calls to process without wiping cookies
    if path.startswith("/static") or path.startswith("/api"):
        return response

    # 1. Non-user web routes must scrub 'user_authenticated'
    allowed_user_paths = ["/payment", "/pending-payments", "/reviewed-requests"]
    if path not in allowed_user_paths:
        response.delete_cookie(key="user_authenticated", path="/")

    # 2. Non-staff web routes must scrub 'staff_authenticated'
    allowed_staff_paths = ["/staff-dashboard"]
    if path not in allowed_staff_paths:
        response.delete_cookie(key="staff_authenticated", path="/")

    return response


@app.middleware("http")
async def inspect_incoming_requests(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/auth/") or path.startswith("/api/staff/"):
        logger.info(f"📥 [REQUEST START] {request.method} {path} | Client IP: {extract_client_ip(request)}")
        logger.info(f"📋 [HEADERS] Content-Type: {request.headers.get('content-type')} | User-Agent: {request.headers.get('user-agent')}")
        
        if request.method in ["POST", "PUT", "PATCH"]:
            body_bytes = await request.body()
            logger.info(f"📦 [RAW BODY]: {body_bytes.decode('utf-8', errors='ignore')}")
            
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            
            request = Request(request.scope, receive=receive)

    response = await call_next(request)
    
    if path.startswith("/api/auth/") or path.startswith("/api/staff/"):
        logger.info(f"📤 [REQUEST END] {request.method} {path} -> Status Code: {response.status_code}")
        
    return response

# --- Validation Exception Handler ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"❌ [422 VALIDATION ERROR] Path: {request.url.path}")
    logger.error(f"❌ [FAILED PAYLOAD]: {body.decode('utf-8', errors='ignore')}")
    logger.error(f"❌ [VALIDATION DETAILS]: {json.dumps(exc.errors())}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"status": "error", "detail": exc.errors(), "body": exc.body}
    )

# --- HTTP Exception Handler ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code >= 400:
        logger.warning(f"⚠️ [HTTP {exc.status_code}] Path: {request.url.path} | Detail: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail}
    )

# --- Global Exception Handler for Uncaught 500 Errors ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"🔥 Unhandled Exception on {request.method} {request.url.path}: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": f"Internal Server Error: {str(exc)}",
            "path": request.url.path
        }
    )

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0, private",
    "Pragma": "no-cache",
    "Expires": "0"
}

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

app.include_router(debug_router)

for folder in ["static", "image_assets", "webpages"]:
    os.makedirs(folder, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Pydantic Schemas ---

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
    user_id: Optional[int] = None
    waste_category: str
    weight_kg: float
    payout_amount: float
    station_id: Optional[str] = None
    payout_method: Optional[str] = "upi"

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
    action: str  
    rejection_reason: Optional[str] = None

class EntryReviewSchema(BaseModel):
    action: str  
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
async def serve_payment(
    user_authenticated: Optional[str] = Cookie(None),
    staff_authenticated: Optional[str] = Cookie(None)
):
    if user_authenticated != "true" or staff_authenticated == "true":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/payment.html", headers=NO_CACHE_HEADERS)

@app.get("/register-payment")
async def serve_register_payment():
    return FileResponse("webpages/register_payment.html")

@app.get("/pending-payments")
async def serve_pending_payments(
    user_authenticated: Optional[str] = Cookie(None),
    staff_authenticated: Optional[str] = Cookie(None)
):
    if user_authenticated != "true" or staff_authenticated == "true":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/pending_payments.html", headers=NO_CACHE_HEADERS)

@app.get("/reviewed-requests")
async def serve_reviewed_requests(
    user_authenticated: Optional[str] = Cookie(None),
    staff_authenticated: Optional[str] = Cookie(None)
):
    if user_authenticated != "true" or staff_authenticated == "true":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/reviewed_requests.html", headers=NO_CACHE_HEADERS)

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
    user_authenticated: Optional[str] = Cookie(None),
    staff_authenticated: Optional[str] = Cookie(None)
):
    logger.info(f"🛡️ [STAFF DASHBOARD CHECK] staff_authenticated={staff_authenticated} | user_authenticated={user_authenticated}")
    if staff_authenticated != "true" or user_authenticated == "true":
        logger.warning("🔒 [STAFF DASHBOARD ACCESS REJECTED] Redirecting to /staff-login")
        return RedirectResponse(url="/staff-login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/staff_dashboard.html", headers=NO_CACHE_HEADERS)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="user_authenticated", path="/")
    response.delete_cookie(key="session_authenticated", path="/")
    response.delete_cookie(key="staff_authenticated", path="/")
    return response

@app.get("/staff-logout")
async def staff_logout():
    response = RedirectResponse(url="/staff-login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="user_authenticated", path="/")
    response.delete_cookie(key="session_authenticated", path="/")
    response.delete_cookie(key="staff_authenticated", path="/")
    return response


# --- Modularized OTP User & Staff Authentication Endpoints ---

@app.post("/api/auth/request-otp")
async def request_otp(data: OTPRequest, request: Request):
    client_ip = extract_client_ip(request)
    logger.info(f"📧 [OTP REQUEST INITIATED] Target Email: {data.email_address} | IP: {client_ip}")
    try:
        result = await process_otp_request(data.email_address, client_ip)
        logger.info(f"✅ [OTP REQUEST SUCCESS] Email dispatched to {data.email_address}")
        return result
    except Exception as e:
        logger.error(f"❌ [OTP REQUEST FAILED] Email: {data.email_address} | Error: {str(e)}", exc_info=True)
        raise e

@app.post("/api/auth/verify-otp")
async def verify_otp_route(data: OTPVerify, request: Request, db: Session = Depends(get_db)):
    client_ip = extract_client_ip(request)
    logger.info(f"🔑 [OTP VERIFY INITIATED] Email: {data.email_address} | Code: {data.otp_code} | IP: {client_ip}")
    try:
        await process_otp_verification(data.email_address, data.otp_code, client_ip)
        
        # Check if the verifying email belongs to staff
        is_staff = db.query(StaffProfile).filter(StaffProfile.email == data.email_address).first()
        logger.info(f"✅ [OTP VERIFY SUCCESS] Granted session to {data.email_address} (Is Staff: {bool(is_staff)})")

        response = JSONResponse(
            content={
                "status": "success", 
                "message": "OTP verified successfully.",
                "is_staff": bool(is_staff)
            }
        )

        if is_staff:
            response.set_cookie(
                key="staff_authenticated",
                value="true",
                httponly=False,
                samesite="lax",
                path="/"
            )
            response.delete_cookie(key="user_authenticated", path="/")
        else:
            response.set_cookie(
                key="user_authenticated",
                value="true",
                httponly=False,
                samesite="lax",
                path="/"
            )
            response.delete_cookie(key="staff_authenticated", path="/")

        return response
    except Exception as e:
        logger.error(f"❌ [OTP VERIFY FAILED] Email: {data.email_address} | Error: {str(e)}", exc_info=True)
        raise e

@app.post("/api/auth/complete-profile")
async def save_user_profile(data: ProfileCreateSchema, response: Response, db: Session = Depends(get_db)):
    try:
        logger.info(f"📝 [PROFILE SAVE INITIATED] Email: {data.email}")
        user = db.query(UserProfile).filter(UserProfile.email == data.email).first()
        
        user_data = data.model_dump()
        user_data["profile_complete"] = False

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
            key="user_authenticated",
            value="true",
            httponly=False,
            samesite="lax",
            path="/"
        )
        response.delete_cookie(key="staff_authenticated", path="/")
        return {"status": "success", "message": "Profile saved successfully!", "user_id": user.id}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [PROFILE SAVE FAILED] Error saving user profile: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database profile update failed: {str(e)}")


# --- User Profile & Data Endpoints ---

@app.get("/api/user/profile")
async def get_user_profile(
    user_id: Optional[int] = Query(None), 
    email: Optional[str] = Query(None), 
    user_authenticated: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    logger.info(f"🔍 [GET PROFILE] user_id: {user_id} | email: {email} | cookie: {user_authenticated}")
    if user_authenticated != "true":
        logger.warning("🔒 [GET PROFILE REJECTED] Cookie user_authenticated != true")
        raise HTTPException(status_code=401, detail="Unauthorized session")

    if not user_id and not email:
        logger.warning("⚠️ [GET PROFILE BAD REQUEST] Missing user_id and email parameters")
        raise HTTPException(status_code=400, detail="Must provide user_id or email query parameter")
    
    query = db.query(UserProfile)
    if user_id:
        user = query.filter(UserProfile.id == user_id).first()
    else:
        user = query.filter(UserProfile.email == email).first()

    if not user:
        logger.warning(f"⚠️ [GET PROFILE NOT FOUND] Query failed for id={user_id}, email={email}")
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
    client_ip = extract_client_ip(request)
    logger.info(f"👮 [STAFF REGISTER] Email: {data.email} | PIN: {data.assigned_pincode} | IP: {client_ip}")

    try:
        existing = db.query(StaffProfile).filter(StaffProfile.email == data.email).first()
        if existing:
            log_auth_event("STAFF_REGISTER", data.email, "FAILED", client_ip, "Duplicate email")
            logger.warning(f"⚠️ [STAFF REGISTER DUPLICATE] {data.email} already exists")
            raise HTTPException(status_code=400, detail="Staff account with this email already exists.")
        
        hashed_password = hash_password(data.password)
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
        logger.info(f"✅ [STAFF REGISTER SUCCESS] Created Staff ID #{new_staff.id}")
        return {"status": "success", "message": "Staff registered successfully!", "staff_id": new_staff.id}
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Schema insertion error on StaffProfile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Staff registration failed due to database schema error: {str(e)}"
        )
        
@app.post("/api/staff/login")
async def login_staff_account(data: StaffLoginSchema, request: Request, db: Session = Depends(get_db)):
    client_ip = extract_client_ip(request)
    logger.info(f"👮 [STAFF LOGIN ATTEMPT] Email: {data.email} | IP: {client_ip}")
    
    staff = db.query(StaffProfile).filter(StaffProfile.email == data.email).first()
    
    if not staff or not verify_password(data.password, staff.password_hash):
        logger.warning(f"❌ [STAFF LOGIN FAILED] Credentials invalid for '{data.email}'")
        log_auth_event("STAFF_LOGIN", data.email, "FAILED", client_ip, "Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid staff credentials.")

    # 1. Trigger OTP dispatch to staff email
    await process_otp_request(data.email, client_ip)
    logger.info(f"📧 [STAFF OTP DISPATCHED] Sent OTP code to {data.email}")

    # 2. Return pending state to frontend without issuing authentication cookies yet
    return {
        "status": "otp_required",
        "message": "Password verified. Please enter the OTP sent to your email.",
        "email": staff.email,
        "staff_id": staff.id,
        "assigned_pincode": staff.assigned_pincode
    }

@app.post("/api/staff/users/{user_id}/review")
async def review_user_profile(
    user_id: int, 
    data: StaffReviewSchema, 
    db: Session = Depends(get_db)
):
    logger.info(f"📋 [STAFF USER REVIEW] Target User ID #{user_id} | Action: {data.action}")
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        logger.warning(f"⚠️ [STAFF USER REVIEW FAILED] User ID #{user_id} not found")
        raise HTTPException(status_code=404, detail=f"User ID #{user_id} not found.")

    user.profile_complete = True if data.action == "approve" else False
    db.commit()
    return {"status": "success", "message": f"User profile status updated to {data.action}"}


# --- Recycling & Waste Transactions ---

@app.post("/api/recycling/entry")
async def add_recycling_entry(data: RecyclingEntrySchema, db: Session = Depends(get_db)):
    logger.info(f"♻️ [RECYCLING ENTRY] User ID: {data.user_id} | Category: {data.waste_category} | Weight: {data.weight_kg}kg")
    try:
        user = None
        if data.user_id:
            user = db.query(UserProfile).filter(UserProfile.id == data.user_id).first()
        
        if not user:
            logger.warning(f"⚠️ [RECYCLING ENTRY FAILED] User ID #{data.user_id} not found")
            raise HTTPException(status_code=404, detail=f"User ID {data.user_id} not found in user_profiles.")
            
        new_entry = RecyclingEntry(
            user_id=user.id,
            waste_category=data.waste_category,
            weight_kg=data.weight_kg,
            payout_amount=data.payout_amount,
            status="pending"
        )
        if hasattr(new_entry, "station_id"):
            setattr(new_entry, "station_id", data.station_id)

        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        
        log_recycling_action("SUBMIT", user.id, data.weight_kg, "PENDING", f"Category: {data.waste_category}")
        logger.info(f"✅ [RECYCLING ENTRY SUCCESS] Created Entry #{new_entry.entry_id}")
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
    user_id: Optional[int] = Query(None), 
    email: Optional[str] = Query(None), 
    db: Session = Depends(get_db)
):
    if not user_id and not email:
        logger.warning("⚠️ [PENDING PAYMENTS BAD REQUEST] Missing user_id and email query parameters")
        raise HTTPException(status_code=400, detail="Must provide user_id or email")
    
    if not user_id and email:
        user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if not user:
            logger.warning(f"⚠️ [PENDING PAYMENTS NOT FOUND] Email '{email}' not found")
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
                "status": getattr(entry, "status", "pending"),
                "created_at": entry.created_at.isoformat() if getattr(entry, "created_at", None) else None
            }
            for entry in entries
        ]
    }

@app.get("/api/recycling/reviewed-requests")
async def get_reviewed_requests(
    user_id: Optional[int] = Query(None), 
    email: Optional[str] = Query(None), 
    db: Session = Depends(get_db)
):
    if not user_id and not email:
        logger.warning("⚠️ [REVIEWED REQUESTS BAD REQUEST] Missing user_id and email parameters")
        raise HTTPException(status_code=400, detail="Must provide user_id or email")
    
    if not user_id and email:
        user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if not user:
            logger.warning(f"⚠️ [REVIEWED REQUESTS NOT FOUND] Email '{email}' not found")
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
    user_id: Optional[int] = Query(None), 
    email: Optional[str] = Query(None), 
    db: Session = Depends(get_db)
):
    if not user_id and email:
        user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if not user:
            logger.warning(f"⚠️ [RECYCLING SUMMARY NOT FOUND] Email '{email}' not found")
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user.id

    entries = db.query(RecyclingEntry).filter(RecyclingEntry.user_id == user_id).all() if user_id else []

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
    search: Optional[str] = Query(None),
    exact_pincode: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    logger.info(f"🔍 [DISTRICT USERS] Pincode: {staff_pincode} | Search: {search} | Exact PIN: {exact_pincode}")
    if len(staff_pincode) < 3:
        logger.warning(f"⚠️ [DISTRICT USERS BAD REQUEST] Pincode '{staff_pincode}' too short")
        raise HTTPException(status_code=400, detail="Staff pincode must be at least 3 digits.")

    district_prefix = staff_pincode[:3]
    
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
    logger.info(f"📊 [SHOW DATA] Requested table: {table_lower}")
    
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
                "weight_kg": float(r.weight_kg),
                "payout_amount": float(r.payout_amount),
                "status": getattr(r, "status", "pending")
            }
            for r in records
        ]
        return {"status": "success", "table": "recycling_entries", "count": len(data), "data": data}

    else:
        logger.warning(f"⚠️ [SHOW DATA BAD REQUEST] Unknown table name '{table}'")
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown table parameter '{table}'."
        )

# --- Household Pending Trash Entries for Staff Review ---
@app.get("/api/admin/user-pending-entries/{user_id}")
async def get_user_pending_entries(user_id: int, db: Session = Depends(get_db)):
    logger.info(f"📋 [USER PENDING ENTRIES] Fetching pending entries for User ID #{user_id}")
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
                "created_at": e.created_at.isoformat() if getattr(e, "created_at", None) else None
            }
            for e in entries
        ]
    }

@app.get("/api/recycling/receipt/{entry_id}")
async def download_receipt(entry_id: int, db: Session = Depends(get_db)):
    logger.info(f"📄 [DOWNLOAD RECEIPT] Generating receipt for Entry #{entry_id}")
    result = db.query(RecyclingEntry, UserProfile).\
        join(UserProfile, RecyclingEntry.user_id == UserProfile.id).\
        filter(RecyclingEntry.entry_id == entry_id).first()

    if not result:
        logger.warning(f"⚠️ [DOWNLOAD RECEIPT NOT FOUND] Entry #{entry_id} not found")
        raise HTTPException(status_code=404, detail=f"Recycling entry #{entry_id} not found.")

    entry, user = result

    receipt_payload = {
        "entry_id": entry.entry_id,
        "user_name": user.full_name or "Valued Customer",
        "user_email": user.email,
        "waste_category": entry.waste_category,
        "weight_kg": float(entry.weight_kg) if entry.weight_kg is not None else 0.0,
        "payout_amount": float(entry.payout_amount) if entry.payout_amount is not None else 0.0,
        "status": getattr(entry, "status", "approved"),
        "station_id": getattr(entry, "station_id", "BIN-DISTRICT-HUB"),
        "created_at": getattr(entry, "created_at", None)
    }

    try:
        pdf_bytes = generate_receipt_pdf(receipt_payload)
    except Exception as e:
        logger.error(f"❌ Error generating PDF for entry #{entry_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to render transaction PDF receipt.")

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
    logger.info(f"📋 [REVIEW RECYCLING ENTRY] Entry #{entry_id} | Action: {data.action} | Staff ID: {data.staff_id}")
    entry = db.query(RecyclingEntry).filter(RecyclingEntry.entry_id == entry_id).first()
    if not entry:
        logger.warning(f"⚠️ [REVIEW ENTRY NOT FOUND] Entry #{entry_id} not found")
        raise HTTPException(status_code=404, detail="Recycling entry not found.")

    new_status = "approved" if data.action == "approve" else "declined"
    
    entry.status = new_status
    if hasattr(entry, "reviewed_by_staff_id"):
        setattr(entry, "reviewed_by_staff_id", data.staff_id)
        
    if data.action == "decline":
        entry.rejection_reason = data.rejection_reason or "Declined by district officer"
        
    db.commit()
    db.refresh(entry)
    
    return {"status": "success", "message": f"Entry #{entry_id} successfully updated to {new_status}."}