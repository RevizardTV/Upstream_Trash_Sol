# tests/payment/test_payment_router.py
import pytest
from unittest.mock import patch, MagicMock
from backend.models import UserProfile, RecyclingEntry

def test_create_payment_order_success(client, db_session):
    user = UserProfile(
        id=1,
        email="paymentuser@example.com",
        full_name="Payment User",
        phone_number="9876543210",
        city="Coimbatore",
        postal_code="641001",
        premise_type="house",
        household_size=2
    )
    db_session.add(user)
    db_session.commit()

    with patch("backend.routers.payment_router.client.order.create") as mock_order_create:
        mock_order_create.return_value = {
            "id": "order_test_abc123",
            "entity": "order",
            "amount": 5000,
            "currency": "INR",
            "status": "created"
        }

        payload = {"amount": 50.0, "user_id": 1}
        response = client.post("/api/payments/create-order", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["order"]["id"] == "order_test_abc123"


def test_verify_payment_signature_success(client, db_session):
    user = UserProfile(
        id=1,
        email="verifyuser@example.com",
        full_name="Verify User",
        phone_number="9876543210",
        city="Coimbatore",
        postal_code="641001",
        premise_type="house",
        household_size=2
    )
    db_session.add(user)
    db_session.commit()

    entry = RecyclingEntry(
        user_id=user.id,
        waste_category="Plastic",
        weight_kg=2.5,
        payout_amount=37.50,
        station_id="BIN-COIMBATORE-01",
        status="pending"
    )
    db_session.add(entry)
    db_session.commit()
    entry_id = entry.entry_id

    with patch("backend.routers.payment_router.client.utility.verify_payment_signature") as mock_verify:
        mock_verify.return_value = True

        payload = {
            "razorpay_order_id": "order_test_abc123",
            "razorpay_payment_id": "pay_test_xyz987",
            "razorpay_signature": "mock_valid_signature_string",
            "entry_id": entry_id
        }

        response = client.post("/api/payments/verify-payment", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        db_session.expire_all()
        updated_entry = db_session.query(RecyclingEntry).filter(RecyclingEntry.entry_id == entry_id).first()
        assert updated_entry.status == "approved"


def test_process_upi_payout_success(client, db_session):
    user = UserProfile(
        id=1,
        email="payoutuser@example.com",
        full_name="Payout User",
        phone_number="9876543210",
        city="Coimbatore",
        postal_code="641001",
        premise_type="house",
        household_size=2
    )
    db_session.add(user)
    db_session.commit()

    # Patch client with a mock object that supports contact/fund_account/payout attributes safely
    mock_client_instance = MagicMock()
    mock_client_instance.contact.create.return_value = {"id": "cont_test_111"}
    mock_client_instance.fund_account.create.return_value = {"id": "fa_test_222"}
    mock_client_instance.payout.create.return_value = {"id": "pout_test_333", "utr": "UTR_TEST_SUCCESS_001"}

    with patch("backend.routers.payment_router.client", mock_client_instance):
        payload = {
            "user_id": 1,
            "upi_id": "testuser@okaxis",
            "amount": 100.0
        }

        response = client.post("/api/payments/payout/upi", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["payout_id"] == "pout_test_333"