import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from fastapi import FastAPI, Depends, HTTPException, Query, status, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
# main.py snippet
import redis.asyncio as redis
from emailSend import send_email
# Import your Redis-backed login helper functions
import py_scripts.login as login
from py_scripts.config import config
import sys
redis_url = os.getenv("REDIS_URL") or getattr(config, "REDIS_URL", None)

if not redis_url:
    print("CRITICAL ERROR: REDIS_URL is missing")
    sys.exit(1)

redis_client = redis.from_url(redis_url, decode_responses=True)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
app = FastAPI()

# Auto-create missing static folders
for folder in ["static", "image_assets", "webpages"]:
    os.makedirs(folder, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Request Schemas
class OTPRequest(BaseModel):
    email_address: EmailStr

class OTPVerify(BaseModel):
    email_address: EmailStr
    otp_code: str

# Authentication Endpoints


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



@app.post("/api/auth/request-otp")
async def request_otp(data: OTPRequest, request: Request):
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Generate OTP and store in Redis
    otp, error = await login.generate_otp(data.email_address, client_ip)
    
    if error or not otp:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail=error or "Failed to generate OTP code."
        )
        
    print(f"OTP:{otp}, ERROR:{error},2.REDIS CLIENT CHECK:{redis_client},REDIS_URL:{redis_url}")
    
    if error:
        raise HTTPException(status_code=429, detail=error)
        
    # Dispatch Email via Resend integration
    try:
        await send_email(
            to_email=data.email_address,
            subject="EcoRecycle - Your Login OTP",
            body=otp  # Pass the raw OTP code so the template formats it correctly
        )
        return {"status": "success", "message": "OTP code dispatched successfully"}
    except Exception as e:
        print(f"Email delivery error context: {e}")
        raise HTTPException(status_code=500, detail="OTP generated, but email delivery failed.")