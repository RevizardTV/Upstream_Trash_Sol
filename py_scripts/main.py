import os
import json
import redis.asyncio as aioredis
from typing import Optional
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="EcoRecycle Platform")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Redis connection
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

# Strict anti-caching HTTP headers
NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0, private",
    "Pragma": "no-cache",
    "Expires": "0"
}

# --- SESSION VERIFICATION HELPERS ---
async def verify_user_session(session_token: Optional[str]) -> bool:
    if not session_token:
        return False
    session_data = await redis_client.get(f"session:{session_token}")
    return session_data is not None

async def verify_staff_session(staff_token: Optional[str]) -> bool:
    if not staff_token:
        return False
    session_data = await redis_client.get(f"staff_session:{staff_token}")
    return session_data is not None

# --- PUBLIC & AUTHENTICATION ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("webpages/index.html")

@app.get("/login", response_class=HTMLResponse)
async def serve_login(session_authenticated: Optional[str] = Cookie(None)):
    # Redirect to app if already authenticated
    if await verify_user_session(session_authenticated):
        return RedirectResponse(url="/payment", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/login.html")

@app.get("/staff-login", response_class=HTMLResponse)
async def serve_staff_login(staff_authenticated: Optional[str] = Cookie(None)):
    if await verify_staff_session(staff_authenticated):
        return RedirectResponse(url="/staff-dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse("webpages/staff_login.html")

@app.get("/logout")
async def logout(response: Response, session_authenticated: Optional[str] = Cookie(None)):
    if session_authenticated:
        await redis_client.delete(f"session:{session_authenticated}")
    
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie("session_authenticated")
    return redirect

# --- PROTECTED APP ROUTES (STRICT NO-CACHE) ---
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

# --- PROTECTED API ENDPOINTS ---
@app.get("/api/user/profile")
async def get_user_profile(session_authenticated: Optional[str] = Cookie(None)):
    if not await verify_user_session(session_authenticated):
        raise HTTPException(status_code=401, detail="Unauthorized session")
    
    session_raw = await redis_client.get(f"session:{session_authenticated}")
    
    # Explicit None check satisfies Pylance and guards against race conditions
    if not session_raw:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
        
    session = json.loads(session_raw)
    return {"status": "success", "profile": session}