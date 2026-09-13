import json
import os
import sys

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
import redis.asyncio as redis
from resend.exceptions import ResendError
from py_scripts.debug import router as debug_router

# Database Imports
from sqlalchemy.orm import Session
from py_scripts.database import Base, UserProfile, RecyclingEntry, engine, get_db

from py_scripts.config import config
from py_scripts.emailSend import send_email
import py_scripts.login as login

# Ensure project directory is in PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Auto-create tables on startup
Base.metadata.create_all(bind=engine)

# Redis Connection Initialization
redis_url = os.getenv("REDIS_URL") or getattr(config, "REDIS_URL", None)
if not redis_url:
    print("CRITICAL ERROR: REDIS_URL is missing")
    sys.exit(1)

redis_client = redis.from_url(redis_url, decode_responses=True)

# App Initialization
app = FastAPI(title="EcoRecycle API")
app.include_router(debug_router)
# Configure CORS Middleware
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

# Auto-create missing static folders & Mount Static Directories
for folder in ["static", "image_assets", "webpages"]:
    os.makedirs(folder, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


# Pydantic Validation Schemas
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
    upi_id: str | None = None




# Page Route Handlers
@app.get("/")
async def serve_home():
    return FileResponse("webpages/index.html")

@app.get("/login")
async def serve_login():
    return FileResponse("webpages/login.html")

@app.get("/payment")
async def serve_payment():
    return FileResponse("webpages/payment.html")

@app.get("/register-payment")
async def serve_register_payment():
    return FileResponse("webpages/register_payment.html")

@app.get("/pending-payments")
async def serve_pending_payments():
    return FileResponse("webpages/pending_payments.html")

@app.get("/payment-info")
async def serve_payment_info():
    return FileResponse("webpages/payment_info.html")

@app.get("/register-profile")
async def serve_profile_registration():
    return FileResponse("webpages/register_profile.html")


# Authentication & Profile Endpoints
@app.post("/api/auth/request-otp")
async def request_otp(data: OTPRequest, request: Request):
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"
    
    otp, error = await login.generate_otp(data.email_address, client_ip)
    
    if error or not otp:
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
        return {"status": "success", "message": "OTP code dispatched successfully"}
        
    except ResendError as re_err:
        print(f"RESEND API DISPATCH ERROR: {re_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resend Mail Error: {str(re_err)}"
        )
    except Exception as e:
        print(f"UNEXPECTED MAIL SYSTEM ERROR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="OTP saved to database, but email delivery service failed."
        )

@app.post("/api/auth/verify-otp")
async def verify_otp_route(data: OTPVerify):
    try:
        is_valid, error = await login.verify_otp(data.email_address, data.otp_code)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=error or "Invalid or expired verification code."
            )
            
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
        print(f"VERIFICATION ROUTE ERROR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying the OTP."
        )

@app.post("/api/auth/complete-profile")
async def save_user_profile(data: ProfileCreateSchema, response: Response, db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.email == data.email).first()
    
    if not user:
        user = UserProfile(**data.model_dump())
        db.add(user)
    else:
        for field, value in data.model_dump().items():
            setattr(user, field, value)
            
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


# Recycling Insertion Endpoint
@app.post("/api/recycling/entry")
async def add_recycling_entry(data: RecyclingEntrySchema, db: Session = Depends(get_db)):
    try:
        user = db.query(UserProfile).filter(UserProfile.id == data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {data.user_id} not found in user_profiles.")
            
        new_entry = RecyclingEntry(**data.model_dump())
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        
        return {
            "status": "success", 
            "message": "Recycling transaction recorded!", 
            "entry_id": new_entry.entry_id
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        print(f"RECYCLING ENTRY ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database insertion failed: {str(e)}")


# Admin & Data Inspection Utilities
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
                "created_at": p.created_at.isoformat() if p.created_at else None
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
                "entry_type": getattr(r, "entry_type", "payout")
            }
            for r in records
        ]
        return {"status": "success", "table": "recycling_entries", "count": len(data), "data": data}

    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown table parameter '{table}'."
        )

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
            "upi_id": user.upi_id
        }
    }

class RecyclingEntrySchema(BaseModel):
    user_id: int
    waste_category: str
    weight_kg: float
    payout_amount: float

    class Config:
        from_attributes = True

@app.get("/api/recycling/pending-payments")
async def get_pending_payments(
    user_id: int = Query(None), 
    email: str = Query(None), 
    db: Session = Depends(get_db)
):
    if not user_id and not email:
        raise HTTPException(status_code=400, detail="Must provide user_id or email")
    
    # Resolve user_id if email was passed
    if not user_id and email:
        user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found")
        user_id = user.id

    # Query entries for the target user
    entries = db.query(RecyclingEntry).filter(RecyclingEntry.user_id == user_id).order_by(RecyclingEntry.entry_id.desc()).all()
    
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
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            }
            for entry in entries
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

    # Financial segregations based on status
    approved_total = sum(float(e.payout_amount) for e in entries if e.status == "approved")
    pending_total = sum(float(e.payout_amount) for e in entries if e.status == "pending")
    total_approved_weight = sum(float(e.weight_kg) for e in entries if e.status == "approved")

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
                "status": e.status,
                "rejection_reason": e.rejection_reason,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in entries
        ]
    }