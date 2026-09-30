import requests

# 1. Login as student1
login_resp = requests.post("http://127.0.0.1:8000/api/auth/login", json={
    "email": "student1@platform.edu",
    "password": "password123"
})
print("Login status:", login_resp.status_code)
token = login_resp.json().get("access_token")

# 2. Submit feedback for hardcoded interview ID 1 (as frontend StudentApplications.tsx does)
headers = {"Authorization": f"Bearer {token}"}
fb_payload = {
    "experience_text": "Challenging interview with questions on data structures.",
    "questions_asked": "Invert binary tree, SQL window functions",
    "difficulty_rating": 4,
    "preparation_time": "2 weeks",
    "suggestions": "Keep practicing DSA questions."
}

resp = requests.post("http://127.0.0.1:8000/api/interviews/1/feedback", json=fb_payload, headers=headers)
print("Submit to /api/interviews/1/feedback Status Code:", resp.status_code)
print("Response Body:", resp.text)

# Also check activity feedback: POST /api/feedback/activity/{id}
resp_act = requests.post("http://127.0.0.1:8000/api/feedback/activity/1", json=fb_payload, headers=headers)
print("Submit to /api/feedback/activity/1 Status Code:", resp_act.status_code)
print("Response Body:", resp_act.text)
