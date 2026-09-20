# tests/test_auth.py
from py_scripts.main import hash_password, verify_password


def test_password_hashing_and_verification():
    """Verify password hashing creates a valid hash and verifies correctly."""
    raw_password = "SecurePassword123!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_unauthenticated_request_returns_401(client):
    """Verify protected endpoints reject requests lacking authorization headers or cookies."""
    # /api/user/profile exists and requires user_authenticated cookie
    response = client.get("/api/user/profile?user_id=1")
    assert response.status_code == 401


def test_invalid_jwt_token_returns_401(client):
    """Verify unauthenticated/invalid requests are rejected on protected endpoints."""
    headers = {"Authorization": "Bearer invalid_token_string"}
    response = client.get("/api/user/profile?user_id=1", headers=headers)
    assert response.status_code == 401