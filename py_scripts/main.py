import os
import json
import redis.asyncio as aioredis
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr

app = FastAPI(title="EcoRecycle Platform")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Redis connection
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

# Strict anti-caching HTTP headers to prevent URL-bar back/forward history bypasses
NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0, private",
    "Pragma": "no-cache",
    "Expires": "0"
}

# --- PYDANTIC SCHEMAS ---
class UserRegisterSchema(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    pincode: str

class StaffRegisterSchema(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    pincode: str
    badge_id: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

# --- SESSION VERIFICATION HELPERS ---
async def verify_user_session(session_token: Optional[str]) -> bool:
    if not session_token:
        return False
    try:
        session_data = await redis_client.get(f"session:{session_token}")
        return session_data is not None
    except Exception as err:
        print(f"Redis session verification error: {err}")
        return False

async def verify_staff_session(staff_token: Optional[str]) -> bool:
    if not staff_token:
        return False
    try:
        session_data = await redis_client.get(f"staff_session:{staff_token}")
        return session_data is not None
    except Exception as err:
        print(f"Redis staff session verification error: {err}")
        return False

# --- PUBLIC WEB PAGES ---
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("webpages/index.html")

@app.get("/register-profile", response_class=HTMLResponse)
async def serve_register_profile():
    return FileResponse("webpages/register_profile.html")

@app.get("/login", response_class=HTMLResponse)
async def serve_login(session_authenticated: Optional[str] = Cookie(None)):
    if await verify_user_session(session_authenticated):
        return RedirectResponse(url="/payment", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/login.html")

@app.get("/staff-login", response_class=HTMLResponse)
async def serve_staff_login(staff_authenticated: Optional[str] = Cookie(None)):
    if await verify_staff_session(staff_authenticated):
        return RedirectResponse(url="/staff-dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/staff_login.html")

@app.get("/logout")
async def logout(response: Response, session_authenticated: Optional[str] = Cookie(None), staff_authenticated: Optional[str] = Cookie(None)):
    if session_authenticated:
        await redis_client.delete(f"session:{session_authenticated}")
    if staff_authenticated:
        await redis_client.delete(f"staff_session:{staff_authenticated}")
    
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie("session_authenticated")
    redirect.delete_cookie("staff_authenticated")
    return redirect

# --- PROTECTED APP PAGES (HANDLES REDIRECTS SAFELY) ---
@app.get("/payment")
async def serve_payment(session_authenticated: Optional[str] = Cookie(None)):
    if not await verify_user_session(session_authenticated):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/payment.html", headers=NO_CACHE_HEADERS)

@app.get("/pending-payments")
async def serve_pending_payments(session_authenticated: Optional[str] = Cookie(None)):
    if not await verify_user_session(session_authenticated):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/payment.html", headers=NO_CACHE_HEADERS)

@app.get("/reviewed-requests")
async def serve_reviewed_requests(session_authenticated: Optional[str] = Cookie(None)):
    if not await verify_user_session(session_authenticated):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/payment.html", headers=NO_CACHE_HEADERS)

@app.get("/staff-dashboard")
async def serve_staff_dashboard(staff_authenticated: Optional[str] = Cookie(None)):
    if not await verify_staff_session(staff_authenticated):
        return RedirectResponse(url="/staff-login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/staff_dashboard.html", headers=NO_CACHE_HEADERS)

# --- USER & STAFF AUTHENTICATION ENDPOINTS ---
@app.post("/api/user/register")
async def register_profile(payload: UserRegisterSchema):
    user_key = f"user:{payload.email}"
    existing = await redis_client.get(user_key)
    if existing:
        raise HTTPException(status_code=400, detail="User email already registered")

    user_data = {
        "full_name": payload.full_name,
        "email": payload.email,
        "password": payload.password, # Note: Use bcrypt/argon2 hashing in production
        "pincode": payload.pincode,
        "role": "user"
    }
    await redis_client.set(user_key, json.dumps(user_data))
    return {"status": "success", "message": "User registered successfully"}

@app.post("/api/staff/register")
async def register_staff(payload: StaffRegisterSchema):
    staff_key = f"staff:{payload.email}"
    existing = await redis_client.get(staff_key)
    if existing:
        raise HTTPException(status_code=400, detail="Staff email already registered")

    staff_data = {
        "full_name": payload.full_name,
        "email": payload.email,
        "password": payload.password,
        "pincode": payload.pincode,
        "badge_id": payload.badge_id,
        "role": "staff"
    }
    await redis_client.set(staff_key, json.dumps(staff_data))
    return {"status": "success", "message": "Staff registered successfully"}

@app.post("/api/user/login")
async def login_user(payload: LoginSchema, response: Response):
    user_raw = await redis_client.get(f"user:{payload.email}")
    if not user_raw or not isinstance(user_raw, str):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_data = json.loads(user_raw)
    if user_data.get("password") != payload.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_token = os.urandom(24).hex()
    await redis_client.set(f"session:{session_token}", json.dumps(user_data), ex=86400) # 24hr expiration

    response.set_cookie(key="session_authenticated", value=session_token, httponly=True, samesite="lax")
    return {"status": "success", "token": session_token, "user": user_data}

@app.post("/api/staff/login")
async def login_staff(payload: LoginSchema, response: Response):
    staff_raw = await redis_client.get(f"staff:{payload.email}")
    if not staff_raw or not isinstance(staff_raw, str):
        raise HTTPException(status_code=401, detail="Invalid staff credentials")

    staff_data = json.loads(staff_raw)
    if staff_data.get("password") != payload.password:
        raise HTTPException(status_code=401, detail="Invalid staff credentials")

    staff_token = os.urandom(24).hex()
    await redis_client.set(f"staff_session:{staff_token}", json.dumps(staff_data), ex=86400)

    response.set_cookie(key="staff_authenticated", value=staff_token, httponly=True, samesite="lax")
    return {"status": "success", "token": staff_token, "staff": staff_data}

# --- PROFILE DATA FETCHERS ---
@app.get("/api/user/profile")
async def get_user_profile(session_authenticated: Optional[str] = Cookie(None)):
    if not await verify_user_session(session_authenticated):
        raise HTTPException(status_code=401, detail="Unauthorized session")
    
    session_raw = await redis_client.get(f"session:{session_authenticated}")
    if not session_raw or not isinstance(session_raw, str):
        raise HTTPException(status_code=401, detail="Session expired or invalid")
        
    session = json.loads(session_raw)
    return {"status": "success", "profile": session}