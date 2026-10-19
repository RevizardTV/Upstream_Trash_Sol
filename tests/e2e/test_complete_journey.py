# tests/e2e/test_complete_journey.py
import re
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.utils import get_latest_otp_from_mailpit

BASE_URL = "http://localhost:5173"

@pytest.mark.e2e
def test_user_journey_home_to_payment(page: Page):
    """
    Flow 1: Home -> User Registration -> OTP Verification -> User Login -> Payment
    """
    # 1. Go to Homepage and wait for network to settle
    page.goto(f"{BASE_URL}/", wait_until="networkidle")
    expect(page).to_have_url(f"{BASE_URL}/")
    
    # 2. Navigate to User Registration (using robust locator or text)
    page.click("text=Register")
    expect(page).to_have_url(re.compile(r".*/register.*"))
    
    # 3. Fill out user registration form
    page.fill("input[name='email']", "user_journey@example.com")
    page.fill("input[name='password']", "SecurePassword123")
    page.click("button[type='submit']")
    
    # 4. Handle OTP verification triggered via Mailpit
    expect(page).to_have_url(re.compile(r".*/verify-otp.*"))
    otp_code = get_latest_otp_from_mailpit()
    page.fill("input[name='otp']", otp_code)
    page.click("button[type='submit']")
    
    # 5. Verify redirect to login upon completion
    expect(page).to_have_url(re.compile(r".*/login.*"))
    
    # 6. Perform User Login
    page.fill("input[name='email']", "user_journey@example.com")
    page.fill("input[name='password']", "SecurePassword123")
    page.click("button[type='submit']")
    
    # 7. Transition to Payment portal with network sync wait
    page.click("text=Proceed to Payment")
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(re.compile(r".*/payment.*"))
    expect(page.locator("body")).to_contain_text("Payment")


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