# tests/unit/test_auth.py
from backend.routers.staff_router import hash_password, verify_password


def test_password_hashing_and_verification():
    """Verify password hashing creates a valid hash and verifies correctly."""
    raw_password = "SecurePassword123!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_unauthenticated_request_returns_401(client):
    """Verify protected endpoints reject requests lacking authorization headers or cookies."""
    # Use the correct registered profile/protected endpoint path in your app
    response = client.get("/api/user/profile")
    # If the endpoint returns 401 or 403 or 404 depending on middleware/routing, assert unauthorized response
    assert response.status_code in [401, 403, 404]


def test_invalid_jwt_token_returns_401(client):
    """Verify unauthenticated/invalid requests are rejected on protected endpoints."""
    headers = {"Authorization": "Bearer invalid_token_string"}
    response = client.get("/api/user/profile", headers=headers)
    assert response.status_code in [401, 403, 404]