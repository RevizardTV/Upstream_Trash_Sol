import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
import redis.asyncio as redis
from fastapi import APIRouter, HTTPException
# Database Engine
from backend.database import engine
from backend.models import Base

# Debug & Core Utilities
from backend.debug import router as debug_router
from backend.config import config

# Import Split Routers
from backend.routers import auth_router, user_router, staff_router, recycling_router

# Logging Utilities
from backend.custom_logging import PerformanceLoggingMiddleware, logger, extract_client_ip

# Ensure parent directory is in sys.path for absolute root execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="EcoRecycle API",
    lifespan=lifespan
)

redis_url = os.getenv("REDIS_URL") or getattr(config, "REDIS_URL", None)
if not redis_url:
    logger.critical("CRITICAL ERROR: REDIS_URL environment variable is missing!")
    sys.exit(1)

redis_client = redis.from_url(redis_url, decode_responses=True)
app.add_middleware(PerformanceLoggingMiddleware)

# --- Middleware ---
@app.middleware("http")
async def enforce_strict_route_cookie_scopes(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api"):
        return await call_next(request)

    response = await call_next(request)
    if path in ["/payment", "/pending-payments", "/reviewed-requests"]:
        response.delete_cookie(key="staff_authenticated", path="/")
    if path in ["/staff-dashboard"]:
        response.delete_cookie(key="user_authenticated", path="/")
    return response

@app.middleware("http")
async def inspect_incoming_requests(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/auth/") or path.startswith("/api/staff/"):
        logger.info(f"📥 [REQUEST START] {request.method} {path} | Client IP: {extract_client_ip(request)}")
    return await call_next(request)

# --- Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"status": "error", "detail": exc.errors(), "body": exc.body}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"🔥 Unhandled Exception: {str(exc)}")
    return JSONResponse(status_code=500, content={"status": "error", "detail": f"Internal Server Error: {str(exc)}"})

# --- CORS & Routers ---
origins = [
    "http://localhost:5173", # SvelteKit Dev Server
    "http://localhost:8000",
    "https://upstream-trash-sol.onrender.com",
    "https://upstream-trash-sol-front.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Debug and Feature Routers
app.include_router(debug_router)
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(staff_router.router)
app.include_router(recycling_router.router)

# Logout Endpoints
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    for cookie in ["user_authenticated", "session_authenticated", "staff_authenticated"]:
        response.delete_cookie(key=cookie, path="/")
    return response

@app.get("/staff-logout")
async def staff_logout():
    response = RedirectResponse(url="/staff-login", status_code=status.HTTP_303_SEE_OTHER)
    for cookie in ["user_authenticated", "session_authenticated", "staff_authenticated"]:
        response.delete_cookie(key=cookie, path="/")
    return response

# --- Redis Inspector Router ---

router = APIRouter(prefix="/api/redis", tags=["Redis Inspector"])

@router.get("/entries")
async def get_redis_entries():
    try:
        keys = await redis_client.keys("*")
        entries = {}
        
        for key in keys:
            key_type = await redis_client.type(key)
            
            if key_type == "string":
                entries[key] = await redis_client.get(key)
            elif key_type == "hash":
                entries[key] = await redis_client.hgetall(key)
            elif key_type == "list":
                entries[key] = await redis_client.lrange(key, 0, -1)
            elif key_type == "set":
                entries[key] = list(await redis_client.smembers(key))
            elif key_type == "zset":
                entries[key] = await redis_client.zrange(key, 0, -1, withscores=True)
            else:
                entries[key] = f"[{key_type} type]"
                
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)