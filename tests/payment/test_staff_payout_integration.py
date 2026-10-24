# tests/staff/test_staff_payout_integration.py
import pytest
from unittest.mock import patch, MagicMock
from backend.models import UserProfile, RecyclingEntry

def test_staff_approval_triggers_upi_payout_integration(client, db_session):
    """
    Integration Test:
    1. Create a user profile with a registered UPI ID.
    2. Create a pending recycling entry for that user.
    3. Simulate staff approval on the entry.
    4. Verify that approving the entry updates status to 'approved' and 
       successfully invokes Razorpay's contact/fund-account/payout workflow.
    """
    # 1. Seed user profile with a valid UPI ID
    user = UserProfile(
        id=10,
        email="integration_user@example.com",
        full_name="Integration User",
        phone_number="9876543210",
        city="Coimbatore",
        postal_code="641001",
        premise_type="house",
        household_size=3,
        upi_id="integration@okaxis",
        profile_complete=True
    )
    db_session.add(user)
    db_session.commit()

    # 2. Seed a pending recycling entry associated with this user
    entry = RecyclingEntry(
        user_id=user.id,
        waste_category="Plastic",
        weight_kg=4.0,
        payout_amount=60.00,
        station_id="BIN-COIMBATORE-05",
        status="pending"
    )
    db_session.add(entry)
    db_session.commit()
    entry_id = entry.entry_id

    # 3. Mock the Razorpay client calls inside the staff router module
    mock_razorpay_instance = MagicMock()
    mock_razorpay_instance.contact.create.return_value = {"id": "cont_live_999"}
    mock_razorpay_instance.fund_account.create.return_value = {"id": "fa_live_888"}
    mock_razorpay_instance.payout.create.return_value = {
        "id": "pout_live_777",
        "utr": "UTR_INTEGRATION_SUCCESS_123"
    }

    with patch("backend.routers.staff_router.razorpay_client", mock_razorpay_instance):
        # 4. Perform the staff review action ('approve') via the test client
        payload = {"action": "approve"}
        response = client.post(f"/api/staff/entries/{entry_id}/review", json=payload)

        # 5. Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert f"Entry #{entry_id}" in data["message"]
        
        # Verify payout details were returned from the automated trigger
        assert data["payout_details"]["status"] == "disbursed"
        assert data["payout_details"]["payout_id"] == "pout_live_777"
        assert data["payout_details"]["utr"] == "UTR_INTEGRATION_SUCCESS_123"

        # 6. Verify database state changed accordingly
        db_session.expire_all()
        updated_entry = db_session.query(RecyclingEntry).filter(RecyclingEntry.entry_id == entry_id).first()
        assert updated_entry.status == "approved"