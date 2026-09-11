import json
import os
import sys

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
import redis.asyncio as redis
from resend.exceptions import ResendError

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

class RecyclingEntrySchema(BaseModel):
    user_id: int
    waste_category: str
    weight_kg: float
    payout_amount: float


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
            httponly=True,
            secure=True,
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
async def save_user_profile(data: ProfileCreateSchema, db: Session = Depends(get_db)):
    print("PROFILE COMPLETION ENACTED")
    user = db.query(UserProfile).filter(UserProfile.email == data.email).first()
    
    if not user:
        user = UserProfile(**data.model_dump())
        db.add(user)
    else:
        for field, value in data.model_dump().items():
            setattr(user, field, value)
            
    db.commit()
    db.refresh(user)
    print("PROFILE DATABASE INSERTION")
    return {"status": "success", "message": "Profile saved successfully!", "user_id": user.id}


# Recycling Insertion Endpoint
@app.post("/api/recycling/entry")
async def add_recycling_entry(data: RecyclingEntrySchema, db: Session = Depends(get_db)):
    # Verify user profile exists first
    user = db.query(UserProfile).filter(UserProfile.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
        
    new_entry = RecyclingEntry(**data.model_dump())
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    
    return {
        "status": "success", 
        "message": "Recycling transaction recorded!", 
        "entry_id": new_entry.entry_id
    }


# Admin & Inspection Utilities
@app.get("/api/auth/redis-inspect")
async def redis_inspect(x_secret_key: str = Header(...)):
    if x_secret_key != config.EM_RESET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        keys = await redis_client.keys("*")
        records = []
        
        for key in keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
            key_type = await redis_client.type(key)
            value = None
            
            try:
                if key_type == "string":
                    raw_val = await redis_client.get(key)
                    value = raw_val.decode('utf-8') if isinstance(raw_val, bytes) else str(raw_val)
                    
                elif key_type == "hash":
                    hash_dict = await redis_client.hgetall(key)
                    value = {
                        (k.decode('utf-8') if isinstance(k, bytes) else str(k)): 
                        (v.decode('utf-8') if isinstance(v, bytes) else str(v)) 
                        for k, v in hash_dict.items()
                    }
                    
                elif key_type == "set":
                    set_members = await redis_client.smembers(key)
                    value = [item.decode('utf-8') if isinstance(item, bytes) else str(item) for item in set_members]
                    
                elif key_type == "list":
                    list_items = await redis_client.lrange(key, 0, -1)
                    value = [item.decode('utf-8') if isinstance(item, bytes) else str(item) for item in list_items]
                    
                else:
                    value = f"[{key_type.upper()} Data Structure]"

            except Exception as parse_err:
                value = f"[Parsing Failure: {str(parse_err)}]"

            ttl = await redis_client.ttl(key)
            
            records.append({
                "key": key_str,
                "value": json.dumps(value) if isinstance(value, (dict, list)) else str(value),
                "ttl_seconds": ttl
            })
            
        return {"status": "success", "records": records}
        
    except Exception as e:
        print(f"CRITICAL REDIS INSPECT ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emergency-reset")
@app.post("/api/auth/emergency-reset")
async def emergency_reset(x_secret_key: str = Header(...)):
    if x_secret_key != config.EM_RESET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    await redis_client.flushall()
    return {"status": "success", "message": "Database cleared successfully"}

# --- Added Database Admin/Inspection Endpoints ---

@app.post("/api/admin/wipe-database")
async def wipe_database(db: Session = Depends(get_db)):
    """Wipes all rows from user_profiles and recycling_entries without dropping tables."""
    try:
        db.query(RecyclingEntry).delete()
        db.query(UserProfile).delete()
        db.commit()
        return {"status": "success", "message": "All data in user_profiles and recycling_entries has been wiped."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to wipe database: {str(e)}")

@app.get("/api/admin/show-profiles")
async def show_profiles(db: Session = Depends(get_db)):
    """Returns a list of all user profiles in the database."""
    profiles = db.query(UserProfile).all()
    return {
        "status": "success",
        "count": len(profiles),
        "profiles": [
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
    }

@app.get("/api/admin/show-data")
async def show_data(table: str = Query(...), db: Session = Depends(get_db)):
    """Returns all rows from the specified table ('Profile' / 'user_profiles' or 'Trash' / 'recycling_entries')."""
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
                "payout_amount": r.payout_amount
            }
            for r in records
        ]
        return {"status": "success", "table": "recycling_entries", "count": len(data), "data": data}

    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown table parameter '{table}'. Valid options: 'Profile', 'Trash', 'user_profiles', 'recycling_entries'."
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