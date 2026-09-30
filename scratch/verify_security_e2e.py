import requests

BASE_URL = "http://127.0.0.1:8000"

def get_token(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    if r.status_code == 200:
        return r.json()["access_token"]
    return None

# Student credentials
s1_token = get_token("student1@platform.edu", "password123")
s2_token = get_token("student2@platform.edu", "password123")
# Faculty credentials
f_cse_token = get_token("faculty.cse@platform.edu", "password123")

print("--- SECURITY VERIFICATION RESULTS ---")

# 1. Student A -> Student B Profile Read
# student1@platform.edu user_id is 8
# student2@platform.edu user_id is 9
headers_s1 = {"Authorization": f"Bearer {s1_token}"}
res = requests.get(f"{BASE_URL}/api/students/9", headers=headers_s1)
print(f"Test 1: Student A (ID 8) reading Student B (ID 9) profile")
print(f"  Expected: 403 Forbidden")
print(f"  Actual status: {res.status_code}")
print(f"  Actual response: {res.json()}")

# 2. Student A -> Student B Profile Edit
res = requests.put(f"{BASE_URL}/api/students/9", json={"skills": "[\"Python\"]"}, headers=headers_s1)
print(f"\nTest 2: Student A (ID 8) writing Student B (ID 9) profile")
print(f"  Expected: 403 Forbidden")
print(f"  Actual status: {res.status_code}")
print(f"  Actual response: {res.json()}")

# 3. Faculty CSE -> ECE Student profile read (or vice versa)
# student2@platform.edu (Radha Joshi) is ECE (dept_id = 2)
# faculty.cse@platform.edu has scope restricted to CSE
headers_f = {"Authorization": f"Bearer {f_cse_token}"}
res = requests.get(f"{BASE_URL}/api/students/9", headers=headers_f)
print(f"\nTest 3: CSE Faculty reading ECE Student profile")
print(f"  Expected: 403 Forbidden")
print(f"  Actual status: {res.status_code}")
print(f"  Actual response: {res.json()}")

# 4. Unauthorized User -> Admin Endpoint
res = requests.get(f"{BASE_URL}/api/students/correction-requests", headers=headers_s1)
print(f"\nTest 4: Student accessing Admin Correction Requests list")
print(f"  Expected: 403 Forbidden")
print(f"  Actual status: {res.status_code}")
print(f"  Actual response: {res.json()}")

# 5. OTP leak testing
res = requests.post(f"{BASE_URL}/api/parent/request-otp", json={"roll_number": 8, "mobile_number": "9876543210"})
print(f"\nTest 5: Parent OTP request leakage inspection")
print(f"  Actual status: {res.status_code}")
print(f"  Actual response data keys: {list(res.json().keys()) if res.status_code == 200 else res.text}")
