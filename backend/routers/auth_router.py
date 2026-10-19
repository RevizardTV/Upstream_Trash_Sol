from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.models import StaffProfile, UserProfile
from backend.database import get_db
from backend.custom_logging import logger
from backend.otp_service import OTPRequest, OTPVerify, extract_client_ip, process_otp_request, process_otp_verification
from backend.schemas import ProfileCreateSchema

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/request-otp")
async def request_otp(data: OTPRequest, request: Request):
    client_ip = extract_client_ip(request)
    logger.info(f"📧 [OTP REQUEST INITIATED] Target Email: {data.email_address} | IP: {client_ip}")
    try:
        return await process_otp_request(data.email_address, client_ip, email_type=data.type or "user")
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ [OTP REQUEST FAILED] Email: {data.email_address} | Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-otp")
async def verify_otp_route(data: OTPVerify, request: Request, db: Session = Depends(get_db)):
    client_ip = extract_client_ip(request)
    logger.info(f"🔑 [OTP VERIFY INITIATED] Email: {data.email_address} | IP: {client_ip}")
    try:
        await process_otp_verification(data.email_address, data.otp_code, client_ip)
        
        is_staff = db.query(StaffProfile).filter(StaffProfile.email == data.email_address).first()
        is_user = db.query(UserProfile).filter(UserProfile.email == data.email_address).first()
        
        response = JSONResponse(content={
            "status": "success", 
            "message": "OTP verified successfully.",
            "is_staff": bool(is_staff),
            "is_user": bool(is_user)
        })

        if is_staff:
            response.set_cookie(key="staff_authenticated", value="true", httponly=False, samesite="lax", path="/")
        if is_user:
            response.set_cookie(key="user_authenticated", value="true", httponly=False, samesite="lax", path="/")

        return response
    except Exception as e:
        logger.error(f"❌ [OTP VERIFY FAILED] Email: {data.email_address} | Error: {str(e)}", exc_info=True)
        raise e

@router.post("/complete-profile")
async def save_user_profile(data: ProfileCreateSchema, response: Response, db: Session = Depends(get_db)):
    try:
        user = db.query(UserProfile).filter(UserProfile.email == data.email).first()
        user_data = data.model_dump()
        user_data["profile_complete"] = True

        if not user:
            user = UserProfile(**user_data)
            db.add(user)
        else:
            for field, value in user_data.items():
                setattr(user, field, value)
                
        db.commit()
        db.refresh(user)

        response.set_cookie(key="user_authenticated", value="true", httponly=False, samesite="lax", path="/")
        return {"status": "success", "message": "Profile saved successfully!", "user_id": user.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database profile update failed: {str(e)}")