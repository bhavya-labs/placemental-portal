import requests
import sys
from datetime import datetime, timedelta

# Login as admin to get auth token
resp_login = requests.post("http://127.0.0.1:8000/api/auth/login", json={
    "email": "admin@platform.edu",
    "password": "password123"
})
if resp_login.status_code != 200:
    print(f"Login failed: {resp_login.text}")
    sys.exit(1)

token = resp_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create a placement activity
activity_data = {
    "activity_name": "Test Workshop",
    "activity_type": "Workshop",
    "date": (datetime.now() + timedelta(days=2)).date().isoformat(),
    "start_time": "10:00 AM",
    "end_time": "12:00 PM",
    "location": "Seminar Hall A",
    "description": "A test workshop to verify calendar status bug.",
    "mandatory": True
}
print("Creating placement activity...")
resp_act = requests.post("http://127.0.0.1:8000/api/activities", json=activity_data, headers=headers)
print(f"Create Activity Status: {resp_act.status_code}")
if resp_act.status_code != 200:
    print(f"Failed to create activity: {resp_act.text}")
    sys.exit(1)

print("Testing /api/calendar/events on dev server after creating activity...")
resp_cal = requests.get("http://127.0.0.1:8000/api/calendar/events", headers=headers)
print(f"Calendar Status: {resp_cal.status_code}")
if resp_cal.status_code != 200:
    print(f"Calendar Error: {resp_cal.text}")
else:
    print("Calendar loaded successfully!")

# Clean up created activity
# Let's delete the activity we created so we leave the database clean.
created_id = resp_act.json().get("id")
if created_id:
    print(f"Deleting test activity {created_id}...")
    requests.delete(f"http://127.0.0.1:8000/api/activities/{created_id}", headers=headers)
