# tests/e2e/test_complete_journey.py
import re
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.utils import get_latest_otp_from_mailpit
import redis,os
BASE_URL = "http://localhost:5173"

def flush_redis_rate_limits():
    """Flushes Redis rate-limiting keys or data after OTP actions."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        client = redis.Redis.from_url(redis_url)
        # Flush all or target specific rate-limit keys if preferred
        client.flushall()
    except Exception as e:
        print(f"⚠️ Could not flush Redis: {e}")

@pytest.mark.e2e
def test_user_journey_home_to_payment(page: Page):
    """
    Flow 1: Home -> User Profile Registration -> OTP Verification -> User Login -> Payment Hub -> Register Waste Entry
    """
    # 1. Go to Homepage and wait for network to settle
    page.goto(f"{BASE_URL}/", wait_until="networkidle")
    expect(page).to_have_url(f"{BASE_URL}/")
    
    # 2. Navigate to Profile Registration (Create One Here / Register Profile)
    page.click("text=Register Profile")
    page.wait_for_url(re.compile(r".*/register-profile.*"))
    
    # 3. Fill out profile registration form matching exact element IDs in ProfileForm.svelte
    page.locator("input[id='email']").fill("delivered@resend.dev")
    page.locator("input[id='fullName']").fill("Test Eco User")
    page.locator("input[id='phoneNumber']").fill("+919876543210")
    page.locator("input[id='city']").fill("Coimbatore")
    page.locator("input[id='postalCode']").fill("641001")
    page.locator("select[id='premiseType']").select_option("apartment")
    page.locator("input[id='householdSize']").fill("3")
    page.locator("input[id='upiId']").fill("testuser@upi")
    
    # Submit profile registration / request OTP
    page.click("button[type='submit']")
    
    # 4. Handle OTP verification step
    page.wait_for_url(re.compile(r".*/register-profile.*"), timeout=5000)
    page.wait_for_selector("input[id='otpInput']", timeout=5000)
    otp_code = get_latest_otp_from_mailpit()
    print(f"DEBUG_MAILPIT_OTP_RESULT: '{otp_code}' (Type: {type(otp_code)})")
    
    page.locator("input[id='otpInput']").fill(str(otp_code))
    page.click("button[type='submit']")
    flush_redis_rate_limits()
    # 5. Perform Portal Login
    page.goto(f"{BASE_URL}/login", wait_until="networkidle")
    page.locator("input[id='emailInput']").fill("delivered@resend.dev")
    page.click("button[type='submit']")
    
    # Handle Login OTP verification
    page.wait_for_url(re.compile(r".*/login.*"))
    login_otp = get_latest_otp_from_mailpit()
    page.locator("input[id='otpInput']").fill(login_otp)
    page.click("button[type='submit']")
    
    # 6. Transition to Payment portal
    page.evaluate("() => { localStorage.setItem('user_email', 'delivered@resend.dev'); localStorage.setItem('user_id', '1'); }")
    expect(page).to_have_url(re.compile(r".*/payment.*"))
    page.wait_for_load_state("networkidle")
    
    # 7. Click Sidebar navigation item and register waste entry
    page.click("text=Register Waste Payment")
    page.fill("input[name='weight_kg']", "12.5")
    page.click("button[type='submit']")
    
    expect(page.locator("body")).to_contain_text("Pending")
'''
@pytest.mark.e2e
def test_staff_journey_home_to_dashboard(page: Page):
    """
    Flow 2: Home -> Staff Registration -> Staff Login -> Staff Dashboard/Payment
    """
    # 1. Go to Homepage
    page.goto(f"{BASE_URL}/", wait_until="networkidle")
    
    # 2. Navigate to Staff Registration/Portal
    page.click("text=Staff Portal")
    expect(page).to_have_url(re.compile(r".*/staff/register.*"))
    
    # 3. Fill out staff registration form
    page.fill("input[name='email']", "staff_journey@example.com")
    page.fill("input[name='password']", "StaffSecure123")
    page.click("button[type='submit']")
    
    # 4. Fetch staff OTP via Mailpit
    expect(page).to_have_url(re.compile(r".*/staff/verify-otp.*"))
    staff_otp = get_latest_otp_from_mailpit()
    page.fill("input[name='otp']", staff_otp)
    page.click("button[type='submit']")
    
    # 5. Staff Login
    page.goto(f"{BASE_URL}/staff/login", wait_until="networkidle")
    page.fill("input[name='email']", "staff_journey@example.com")
    page.fill("input[name='password']", "StaffSecure123")
    page.click("button[type='submit']")
    
    # 6. Verify entry into Staff Dashboard / Payment view
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(re.compile(r".*/staff/dashboard.*"))
    expect(page.locator("body")).to_contain_text("Staff Portal")


@pytest.mark.e2e
def test_route_guard_url_jumping_prevention(page: Page):
    """
    Flow 3: URL jumping prevention / Route guards
    If unauthenticated users try to access payment or staff dashboards directly via URL,
    they must be booted/redirected to their respective login screens.
    """
    # Attempt 1: Unauthorized user tries to jump straight to the payment URL
    page.goto(f"{BASE_URL}/payment", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r".*/(login|auth/login).*"))
    
    # Attempt 2: Unauthorized user tries to jump straight to the staff dashboard URL
    page.goto(f"{BASE_URL}/staff/dashboard", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r".*/staff/(login|auth).*"))
    '''