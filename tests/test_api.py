from unittest.mock import patch
import sys,os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
def test_home_route(client):
    """Verify that the home page returns 200 OK."""
    response = client.get("/")
    assert response.status_code == 200

def test_admin_show_data_unauthorized(client):
    """Ensure admin endpoints block access when secret header is missing."""
    response = client.get("/api/admin/show-profiles")
    assert response.status_code == 403

def test_admin_show_data_authorized(client):
    """Ensure admin access works when correct EM_RESET_KEY header is provided."""
    headers = {"x-admin-secret": "test_secret_key"}
    
    with patch("py_scripts.config.config.EM_RESET_KEY", "test_secret_key"):
        response = client.get("/api/admin/show-profiles", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

def test_recycling_entry_user_not_found(client):
    """Verify system returns 404 when submitting trash for a non-existent user."""
    payload = {
        "user_id": 9999,
        "waste_category": "Plastic",
        "weight_kg": 2.5,
        "payout_amount": 10.0
    }
    response = client.post("/api/recycling/entry", json=payload)
    assert response.status_code == 404