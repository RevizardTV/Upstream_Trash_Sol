from pydantic import BaseModel, EmailStr
from fastapi import HTTPException, status, Request
from resend.exceptions import ResendError
from typing import Optional
from backend import login
from backend.emailSend import send_email
from backend.custom_logging import log_auth_event, logger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
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

    resend_key = os.getenv("RESEND_API_KEY", "mock_resend_key")
    subject = "EcoRecycle Staff Portal Code" if email_type == "staff" else "EcoRecycle Verification Code"

    # If using mock key or local environment, route directly to Mailpit via SMTP (port 1025)
    if resend_key == "mock_resend_key" or os.getenv("ENVIRONMENT") == "test":
        try:
            msg = MIMEMultipart()
            msg["From"] = "onboarding@resend.dev"
            msg["To"] = email_address
            msg["Subject"] = subject
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>EcoRecycle Verification</h2>
                <p>Your verification code is:</p>
                <h1 style="color: #10b981; letter-spacing: 4px;">{otp}</h1>
                <p>This code expires in 60 seconds.</p>
            </div>
            """
            msg.attach(MIMEText(html_content, "html"))

            # Connect to Mailpit local SMTP server
            smtp_host = os.getenv("SMTP_HOST", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", 1025))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.sendmail("onboarding@resend.dev", [email_address], msg.as_string())
                
            logger.info(f"📧 [MAILPIT DISPATCH] OTP email sent locally to {email_address} via Mailpit ({smtp_host}:{smtp_port})")
            return {"status": "success", "message": "OTP code dispatched successfully"}
            
        except Exception as smtp_err:
            logger.error(f"Failed to deliver OTP via local Mailpit SMTP: {str(smtp_err)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to send local verification email."
            )

    # Production flow using Resend API
    try:
        await send_email(
            to_email=email_address,
            subject=subject,
            body=otp,
            email_type=email_type
        )
    except ResendError as e:
        logger.error(f"Failed to deliver OTP email via Resend to {email_address}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send verification email. Please try again shortly."
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