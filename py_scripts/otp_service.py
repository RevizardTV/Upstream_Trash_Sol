# py_scripts/otp_service.py
from pydantic import BaseModel, EmailStr
from fastapi import HTTPException, status, Request
from resend.exceptions import ResendError

from py_scripts import login
from py_scripts.emailSend import send_email
from py_scripts.logging import log_auth_event, logger

# Schemas
class OTPRequest(BaseModel):
    email_address: EmailStr

class OTPVerify(BaseModel):
    email_address: EmailStr
    otp_code: str


def extract_client_ip(request: Request) -> str:
    """Helper to get client IP behind reverse proxies like Render."""
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        return client_ip.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


async def process_otp_request(email_address: str, client_ip: str):
    """Generates an OTP code and dispatches it via email."""
    otp, error = await login.generate_otp(email_address, client_ip)
    
    if error or not otp:
        log_auth_event("OTP_REQUEST", email_address, "FAILED", client_ip, error or "Rate limit exceeded")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail=error or "Failed to generate OTP code."
        )
    
    try:
        await send_email(
            to_email=email_address,
            subject="EcoRecycle - Your Login OTP",
            body=otp
        )
        log_auth_event("OTP_REQUEST", email_address, "SUCCESS", client_ip, "OTP sent via email")
        return {"status": "success", "message": "OTP code dispatched successfully"}
        
    except ResendError as re_err:
        log_auth_event("OTP_REQUEST", email_address, "ERROR", client_ip, f"Resend API Error: {str(re_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resend Mail Error: {str(re_err)}"
        )
    except Exception as e:
        log_auth_event("OTP_REQUEST", email_address, "ERROR", client_ip, f"Mail delivery error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="OTP saved to database, but email delivery service failed."
        )


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