from pydantic import BaseModel, EmailStr
from fastapi import HTTPException, status, Request
from resend.exceptions import ResendError
from typing import Optional
from py_scripts import login
from py_scripts.emailSend import send_email
from py_scripts.custom_logging import log_auth_event, logger

# Schemas
class OTPRequest(BaseModel):
    email_address: EmailStr
    type: Optional[str] = "user"

class OTPVerify(BaseModel):
    email_address: EmailStr
    otp_code: str


def extract_client_ip(request: Request) -> str:
    """Helper to get client IP behind reverse proxies like Render."""
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        return client_ip.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


async def process_otp_request(email_address: str, client_ip: str, email_type: str = "user"):
    otp, error = await login.generate_otp(email_address, client_ip)
    if error or not otp:
        raise HTTPException(status_code=429, detail=error)

    await send_email(
        to_email=email_address,
        subject="EcoRecycle Staff Portal Code" if email_type == "staff" else "EcoRecycle Verification Code",
        body=otp,
        email_type=email_type
    )
    return {"status": "success", "message": "OTP code dispatched successfully"}


async def process_otp_verification(email_address: str, otp_code: str, client_ip: str):
    """Validates the OTP code against stored records."""
    try:
        is_valid, error = await login.verify_otp(email_address, otp_code)
        
        if not is_valid:
            log_auth_event("OTP_VERIFY", email_address, "FAILED", client_ip, error or "Invalid code")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=error or "Invalid or expired verification code."
            )
            
        log_auth_event("OTP_VERIFY", email_address, "SUCCESS", client_ip, "Session cookie granted")
        return True
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"OTP Verification failure for {email_address}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying the OTP."
        )