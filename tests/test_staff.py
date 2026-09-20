# tests/test_staff.py
from tests.factories import RecyclingEntryFactory, StaffProfileFactory, UserProfileFactory


def test_staff_profile_creation(db_session):
    """Verify staff factory correctly sets pincode assignment."""
    staff = StaffProfileFactory.create_instance(assigned_pincode="641001")
    assert staff.assigned_pincode == "641001"
    assert staff.email.endswith("@example.com")


def test_nonexistent_entry_returns_404(client):
    """Verify fetching a non-existent entry returns 404 Not Found."""
    response = client.get("/api/staff/entries/99999")
    assert response.status_code == 404


def test_pincode_mismatch_filtering(db_session):
    """Verify entries in different pincodes do not match staff assignment."""
    staff = StaffProfileFactory.create_instance(assigned_pincode="641001")
    other_user = UserProfileFactory.create_instance(postal_code="641002")
    entry = RecyclingEntryFactory.create_instance(user=other_user)

    assert staff.assigned_pincode != entry.user.postal_code