# emailSend.py
import resend
from resend.exceptions import ResendError
from py_scripts.config import config

def get_user_email_template(otp_code: str) -> str:
    """Template for Household User Login / Profile Verification"""
    return f"""
    <div style="font-family: Arial, sans-serif; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; max-width: 500px;">
        <h2 style="color: #059669; margin-top: 0;">EcoRecycle — Verification Code</h2>
        <p style="color: #334155; font-size: 14px;">Hello! Use the code below to verify your household account.</p>
        
        <div style="font-size: 28px; font-weight: bold; color: #059669; letter-spacing: 4px; background: #f0fdf4; padding: 12px 20px; border-radius: 6px; display: inline-block; margin: 16px 0;">
            {otp_code}
        </div>
        
        <p style="color: #64748b; font-size: 12px; margin-bottom: 0;">
            This code expires in 60 seconds. If you did not request this, please ignore this email.
        </p>
    </div>
    """

def get_staff_email_template(otp_code: str) -> str:
    """Template for Staff Authorization & Registration"""
    return f"""
    <div style="font-family: Arial, sans-serif; padding: 24px; border: 1px solid #cbd5e1; border-radius: 8px; max-width: 500px; background-color: #f8fafc;">
        <h2 style="color: #0f172a; margin-top: 0;">EcoRecycle Staff Portal</h2>
        <p style="color: #334155; font-size: 14px;">Official Authorization Request for District Staff Registration.</p>
        
        <div style="font-size: 28px; font-weight: bold; color: #2563eb; letter-spacing: 4px; background: #eff6ff; padding: 12px 20px; border: 1px solid #bfdbfe; border-radius: 6px; display: inline-block; margin: 16px 0;">
            {otp_code}
        </div>
        
        <p style="color: #64748b; font-size: 12px; margin-bottom: 0;">
            Security Notice: Do not share this operational security key. Code expires in 60 seconds.
        </p>
    </div>
    """

resend.api_key = config.RESEND_API_KEY

async def send_email(to_email: str, subject: str, body: str, email_type: str = "user"):
    """
    Sends an email securely using Resend's Async SDK.
    `email_type` can be 'user' or 'staff'.
    """
    template = get_staff_email_template(body) if email_type == "staff" else get_user_email_template(body)

    try:
        params: resend.Emails.SendParams = {
            "from": "EcoRecycle Auth <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": template
        }
        
        email_response = await resend.Emails.send_async(params)
        print(f"RESEND SUCCESS: [{email_type.upper()}] Email sent successfully! ID: {email_response.get('id')}")
        return email_response
        
    except ResendError as e:
        print(f"RESEND UTILITY ERROR: Failed to dispatch mail via API. Details: {e}")
        raise e