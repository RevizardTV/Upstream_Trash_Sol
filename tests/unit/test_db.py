from backend.models import UserProfile, StaffProfile
from sqlalchemy import text
def test_database_connection(db_session):
    """Verifies that the database engine accepts queries."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1

def test_user_profile_creation(db_session):
    """Tests creating and querying a UserProfile entity."""
    user = UserProfile(
        email="alex.morgan@example.com",
        full_name="Alex Morgan",
        phone_number="+919876543210",
        city="Coimbatore",
        postal_code="641001",
        premise_type="house",
        household_size=2
    )
    db_session.add(user)
    db_session.commit()
    
    saved_user = db_session.query(UserProfile).filter(UserProfile.email == "alex.morgan@example.com").first()
    assert saved_user is not None
    assert saved_user.full_name == "Alex Morgan"
    assert saved_user.postal_code == "641001"