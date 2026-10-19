# tests/e2e/utils.py
import re
import httpx

def get_latest_otp_from_mailpit(mailpit_api_url: str = "http://localhost:8025") -> str:
    """Fetches the latest email from Mailpit API and extracts a 6-digit OTP."""
    response = httpx.get(f"{mailpit_api_url}/api/v1/messages")
    response.raise_for_status()
    data = response.json()
    
    messages = data.get("messages", [])
    if not messages:
        raise AssertionError("No emails found in Mailpit inbox.")
    
    latest_id = messages[0]["ID"]
    msg_response = httpx.get(f"{mailpit_api_url}/api/v1/message/{latest_id}")
    msg_response.raise_for_status()
    msg_data = msg_response.json()
    
    body = msg_data.get("Text") or msg_data.get("HTML") or ""
    match = re.search(r"\b\d{6}\b", body)
    if not match:
        raise AssertionError(f"Could not find 6-digit OTP in email body: {body}")
        
    return match.group(0)