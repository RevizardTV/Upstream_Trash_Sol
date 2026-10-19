# tests/e2e/utils.py
import re
import time
import httpx

def verify_mailpit_health(mailpit_api_url: str = "http://localhost:8025") -> bool:
    """Smoke test to verify Mailpit is running and reachable."""
    try:
        response = httpx.get(f"{mailpit_api_url}/api/v1/messages", timeout=3.0)
        response.raise_for_status()
        return True
    except Exception as e:
        raise RuntimeError(f"Mailpit health check failed: {e}. Ensure Mailpit is running locally on port 8025.")

def clear_mailpit_inbox(mailpit_api_url: str = "http://localhost:8025"):
    """Wipes all messages from the Mailpit inbox to prevent stale data."""
    try:
        httpx.delete(f"{mailpit_api_url}/api/v1/messages")
    except Exception:
        pass

def get_latest_otp_from_mailpit(mailpit_api_url: str = "http://localhost:8025", timeout: int = 10, clear_first: bool = False) -> str:
    """
    Fetches the latest email from Mailpit API with polling/retries, extracts a 6-digit OTP.
    Set clear_first=True if you want to wipe old/stale emails before waiting for the new one.
    """
    verify_mailpit_health(mailpit_api_url)
    
    if clear_first:
        clear_mailpit_inbox(mailpit_api_url)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(f"{mailpit_api_url}/api/v1/messages")
            response.raise_for_status()
            data = response.json()
            
            messages = data.get("messages", [])
            if messages:
                # Grab the absolute latest message
                latest_id = messages[0]["ID"]
                msg_response = httpx.get(f"{mailpit_api_url}/api/v1/message/{latest_id}")
                msg_response.raise_for_status()
                msg_data = msg_response.json()
                
                body = msg_data.get("Text") or msg_data.get("HTML") or ""
                match = re.search(r"\b\d{6}\b", body)
                
                if match:
                    otp = match.group(0)
                    print(f"Successfully extracted fresh OTP from Mailpit: {otp}")
                    
                    # Delete the message immediately so it's never reused
                    httpx.delete(f"{mailpit_api_url}/api/v1/message/{latest_id}")
                    return otp
        except Exception as err:
            print(f"Waiting for fresh email in Mailpit inbox... ({err})")
            
        time.sleep(0.5) # Poll every 500ms
        
    raise AssertionError(f"No emails or 6-digit OTP found in Mailpit inbox after {timeout} seconds.")