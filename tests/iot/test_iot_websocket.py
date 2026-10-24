# tests/unit/test_iot_websocket.py
import pytest
from backend.database import get_db
from backend.main import app 
from fastapi.testclient import TestClient
from backend.models import UserProfile
from backend.routers.websocket_router import manager  # Imports the real manager

def test_sensor_api_submission(client, db_session):
    """Test 1: Verify the sensor HTTP endpoint processes telemetry correctly."""
    
    # 1. Seed user 1 in the test database session
    user = UserProfile(
        id=1,
        email="testuser@example.com",
        full_name="Test User",
        phone_number="9876543210",
        city="Coimbatore",
        postal_code="641001",
        premise_type="house",
        household_size=2
    )
    db_session.add(user)
    db_session.commit()

    # 2. Override get_db to ensure the TestClient uses our active test session
    app.dependency_overrides[get_db] = lambda: db_session

    payload = {
        "user_id": 1,
        "waste_category": "Plastic",
        "weight_kg": 3.5,
        "payout_amount": 52.50,
        "station_id": "BIN-COIMBATORE-01",
        "payout_method": "upi"
    }
    
    response = client.post("/api/recycling/entry", json=payload)
    
    # Clear override after request
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Recycling transaction recorded!"


def test_websocket_sensor_broadcast(client, db_session):
    """Test 2: Verify that when a sensor payload arrives, it broadcasts via WebSockets."""
    
    # 1. Seed a user with id=1 so foreign key lookups pass
    user = UserProfile(
        id=1,
        email="testuser@example.com",
        full_name="Test User",
        phone_number="9876543210",
        city="Coimbatore",
        postal_code="641001",
        premise_type="house",
        household_size=2
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 2. Connect to the WebSocket endpoint using TestClient
    with client.websocket_connect("/ws/chat") as websocket:
        
        payload = {
            "user_id": 1,
            "waste_category": "Metal",
            "weight_kg": 2.5,
            "payout_amount": 112.50,
            "station_id": "BIN-COIMBATORE-08",
            "payout_method": "upi"
        }
        
        # 3. Trigger the recycling entry API call
        res = client.post("/api/recycling/entry", json=payload)
        
        if res.status_code != 200:
            print("API Error Response:", res.json())
            
        assert res.status_code == 200

        # 4. Receive the broadcasted message from the websocket connection
        data = websocket.receive_json()
        assert data["type"] == "IOT_WEIGHT_UPDATE"
        assert data["waste_category"] == "Metal"
        assert data["weight_kg"] == 2.5
        assert data["station_id"] == "BIN-COIMBATORE-08"