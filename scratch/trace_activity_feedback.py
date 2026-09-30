from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.auth import create_access_token
import traceback

client = TestClient(app, raise_server_exceptions=False)
token = create_access_token(data={"sub": "student1@platform.edu", "role": "student"})
headers = {"Authorization": f"Bearer {token}"}

fb_payload = {
    "experience_text": "Challenging interview with questions on data structures.",
    "questions_asked": "Invert binary tree, SQL window functions",
    "difficulty_rating": 4,
    "preparation_time": "2 weeks",
    "suggestions": "Keep practicing DSA questions."
}

resp = client.post("/api/feedback/activity/1", json=fb_payload, headers=headers)
print("Status code:", resp.status_code)
print("Response text:", resp.text)

# Now let's run with raise_server_exceptions=True to get full traceback!
try:
    client_raise = TestClient(app, raise_server_exceptions=True)
    client_raise.post("/api/feedback/activity/1", json=fb_payload, headers=headers)
except Exception:
    traceback.print_exc()
