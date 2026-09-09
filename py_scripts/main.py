import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr

# Import your Redis-backed login helper functions
from py_scripts.login import generate_otp, verify_otp

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
@app.post("/api/auth/request-otp")
async def request_otp(payload: OTPRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    otp, err = await generate_otp(payload.email_address, client_ip)
    if err:
        raise HTTPException(status_code=400, detail=err)
    
    # Send email via emailSend.py or print to console for development
    print(f"Generated OTP for {payload.email_address}: {otp}")
    return {"status": "success", "message": "OTP generated successfully."}

@app.post("/api/auth/verify-otp")
async def verify_otp_endpoint(payload: OTPVerify):
    is_valid, err = await verify_otp(payload.email_address, payload.otp_code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err or "Invalid OTP.")
    return {"status": "success", "message": "Authenticated successfully."}

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