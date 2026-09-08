# mail.py
import resend
from resend.exceptions import ResendError
from config import config

def get_email_template(otp_code: str):
    return f"""
    <div style="font-family: sans-serif; padding: 20px; border: 1px solid #eee;">
        <h2 style="color: #333;">Your Verification Code</h2>
        <p>Hello! Use the code below to sign in to <b>cadWebSurf</b>.</p>
        
        <div style="font-size: 24px; font-weight: bold; color: #007bff; margin: 20px 0;">
            {otp_code}
        </div>
        
        <p style="color: #666; font-size: 12px;">
            This code expires in 1 minute. If you didn't request this, 
            you can safely ignore this email.
        </p>
    </div>
    """

# Automatically pull the API key from your environment
resend.api_key = config.RESEND_API_KEY

async def send_email(to_email: str, subject: str, body: str):
    """Sends an email securely over HTTP using Resend's Async SDK."""
    try:
        params: resend.Emails.SendParams = {
            # While testing, you MUST use this 'from' address unless you verify a custom domain
            "from": "Auth System for CAD SURF WEB <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": get_email_template(body) # Resend accepts raw text or HTML layout fields
        }
        
        # Non-blocking async API call
        email_response = await resend.Emails.send_async(params)
        print(f"RESEND SUCCESS: Email sent successfully! ID: {email_response.get('id')}")
        return email_response
        
    except ResendError as e:
        print(f"RESEND UTILITY ERROR: Failed to dispatch mail via API. Details: {e}")
        raise e