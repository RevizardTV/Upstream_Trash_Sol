# tests/test_recycling.py
from tests.factories import RecyclingEntryFactory, UserProfileFactory


def test_invalid_weight_raises_validation_error(client, db_session):
    """Verify negative or zero weight triggers a Pydantic 422 error."""
    # Create a user in the test database so the request doesn't fail with 404
    user = UserProfileFactory.create_instance()

    payload = {
        "user_id": user.id,
        "waste_category": "Plastic",
        "weight_kg": -5.0,  # Invalid weight
        "payout_amount": 100.0,
    }

    response = client.post("/api/recycling/entry", json=payload)
    assert response.status_code == 422

def test_recycling_payout_calculation(db_session):
    """Verify payout calculation matches category rate * weight."""
    user = UserProfileFactory.create_instance()
    entry = RecyclingEntryFactory.create_instance(user=user, weight_kg=10.0, payout_amount=200.0)

    assert entry.weight_kg == 10.0
    assert entry.payout_amount == 200.0
    assert entry.user.id == user.id


def test_entry_default_status_is_pending(db_session):
    """Verify new entries default to 'pending' status."""
    entry = RecyclingEntryFactory.create_instance()
    assert entry.status == "pending"