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
from py_scripts.emailSend import send_email
import json
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




    
@app.get("/api/auth/redis-inspect")
async def redis_inspect(x_secret_key: str = Header(...)):
    if x_secret_key != config.EM_RESET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        keys = await redis_client.keys("*")
        records = []
        
        for key in keys:
            # Handle key decoding if the key itself comes back as bytes
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
    
from resend.exceptions import ResendError

# Emergency Reset Endpoints (Supports both endpoint paths)
@app.post("/emergency-reset")
@app.post("/api/auth/emergency-reset")
async def emergency_reset(x_secret_key: str = Header(...)):
    if x_secret_key != config.EM_RESET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    await redis_client.flushall()
    return {"status": "success", "message": "Database cleared successfully"}

# Request OTP with detailed Resend error reporting
@app.post("/api/auth/request-otp")
async def request_otp(data: OTPRequest, request: Request):
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"
    
    otp, error = await login.generate_otp(data.email_address, client_ip)
    
    if error or not otp:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error or "Failed to generate OTP")
        
    try:
        await send_email(
            to_email=data.email_address,
            subject="EcoRecycle - Your Verification Code",
            body=otp
        )
        return {"status": "success", "message": "OTP code dispatched successfully"}
    except ResendError as re_err:
        print(f"CRITICAL RESEND API ERROR: {re_err}")
        raise HTTPException(
            status_code=500, 
            detail=f"Email dispatch failed: Check RESEND_API_KEY or verified sender domain. ({str(re_err)})"
        )
    except Exception as e:
        print(f"Unexpected Email Error: {e}")
        raise HTTPException(status_code=500, detail="OTP generated, but email delivery failed.")