import time
import random
import requests

# FastAPI Backend Endpoint
API_URL = "http://localhost:8000/api/recycling/entry"

# Simulated Smart Bin configurations
STATION_IDS = ["BIN-COIMBATORE-01", "BIN-COIMBATORE-08", "BIN-COIMBATORE-12"]
CATEGORIES = [
    {"label": "Plastic", "rate": 15.00, "type": "payout"},
    {"label": "Metal", "rate": 45.00, "type": "payout"},
    {"label": "Paper", "rate": 8.00, "type": "payout"},
    {"label": "E-Waste", "rate": 65.00, "type": "payout"},
    {"label": "Landfill", "rate": -12.00, "type": "charge"}
]

def simulate_sensor_reading(user_id: int):
    """Simulates a smart weight sensor triggering a drop-off event."""
    station_id = random.choice(STATION_IDS)
    category = random.choice(CATEGORIES)
    
    # Generate a realistic weight between 0.5 kg and 10.0 kg
    weight_kg = round(random.uniform(0.5, 10.0), 2)
    payout_amount = category["rate"] * weight_kg

    payload = {
        "user_id": user_id,
        "waste_category": category["label"],
        "weight_kg": weight_kg,
        "payout_amount": round(payout_amount, 2),
        "station_id": station_id,
        "payout_method": "upi"
    }

    print(f"[MQTT SIMULATOR] Sensor triggered at {station_id}:")
    print(f" -> Category: {category['label']} | Weight: {weight_kg} kg | Total: ₹{payout_amount:.2f}")

    try:
        # Posting to your FastAPI backend endpoint matching your Svelte form logic
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print("[SUCCESS] Simulated IoT payload successfully processed by backend.\n")
        else:
            print(f"[ERROR] Backend rejected payload: {response.text}\n")
    except Exception as e:
        print(f"[CONNECTION ERROR] Could not reach backend: {e}\n")

if __name__ == "__main__":
    # Replace with a valid test user ID present in your database
    TEST_USER_ID = 1 
    
    print("--- Smart Waste Bin MQTT Simulator Started ---")
    print("Simulating sensor telemetry drops every 10 seconds. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            simulate_sensor_reading(user_id=TEST_USER_ID)
            time.sleep(10) # Simulate a drop event every 10 seconds
    except KeyboardInterrupt:
        print("\nSimulator stopped.")