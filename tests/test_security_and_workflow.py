# tests/test_security_and_workflow.py
import pytest
from py_scripts.database import RecyclingEntry
from tests.factories import UserProfileFactory, StaffProfileFactory, RecyclingEntryFactory


def test_verify_otp_invalid_code(client):
    """Ensure invalid OTP codes are rejected."""
    response = client.post(
        "/api/auth/verify-otp",
        json={"email_address": "test@example.com", "otp_code": "000000"}
    )
    assert response.status_code in [400, 422]
    assert "user_authenticated" not in response.cookies


def test_recycling_entry_workflow(client, db_session):
    # Pylance accurately infers user as UserProfile
    user = UserProfileFactory.create_instance()

    response = client.post("/api/recycling/entry", json={
        "user_id": user.id,
        "waste_category": "Plastic",
        "weight_kg": 10.0,
        "payout_amount": 200.0
    })

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    entry_id = response.json()["entry_id"]
    db_entry = db_session.query(RecyclingEntry).get(entry_id)
    
    assert db_entry is not None
    assert db_entry.status == "pending"


def test_staff_entry_review_workflow(client, db_session):
    # Pylance accurately infers all model types without StubObject warnings
    user = UserProfileFactory.create_instance(postal_code="641001")
    staff = StaffProfileFactory.create_instance(assigned_pincode="641001")
    entry = RecyclingEntryFactory.create_instance(user=user, status="pending")

    review_resp = client.post(f"/api/staff/entries/{entry.entry_id}/review", json={
        "action": "approve",
        "staff_id": staff.id
    })
    assert review_resp.status_code == 200

    db_session.refresh(entry)
    assert entry.status == "approved"
    assert entry.reviewed_by_staff_id == staff.id