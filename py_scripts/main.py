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

from py_scripts.config import config
from py_scripts.emailSend import send_email
import py_scripts.login as login

# Ensure project directory is in PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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


# Pydantic Schemas
class OTPRequest(BaseModel):
    email_address: EmailStr

class OTPVerify(BaseModel):
    email_address: EmailStr
    otp_code: str


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


# Authentication Endpoints
@app.post("/api/auth/request-otp")
async def request_otp(data: OTPRequest, request: Request):
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"
    
    # 1. Generate OTP and store in Redis
    otp, error = await login.generate_otp(data.email_address, client_ip)
    
    if error or not otp:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail=error or "Failed to generate OTP code."
        )
    
    # 2. Dispatch email with Resend
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

# Page Route Handlers
@app.get("/register-payment")
async def serve_register_payment():
    return FileResponse("webpages/register_payment.html")

@app.get("/pending-payments")
async def serve_pending_payments():
    return FileResponse("webpages/pending_payments.html")

@app.get("/payment-info")
async def serve_payment_info():
    return FileResponse("webpages/payment_info.html")

