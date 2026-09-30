import requests
import sys

resp_login = requests.post("http://127.0.0.1:8000/api/auth/login", json={
    "email": "student1@platform.edu",
    "password": "password123"
})
print("Login status:", resp_login.status_code)
if resp_login.status_code == 200:
    data = resp_login.json()
    print("Login Response keys:", data.keys())
    print("Login Response details: Role:", data.get("role"), "| Name:", data.get("name"), "| Email:", data.get("email"))
    
    # Get profile details
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Fetch profile using /api/auth/profile
    resp_prof = requests.get("http://127.0.0.1:8000/api/auth/profile", headers=headers)
    print("Profile API Status:", resp_prof.status_code)
    if resp_prof.status_code == 200:
        prof_data = resp_prof.json()
        print("Profile details Name:", prof_data.get("name"), "| Role:", prof_data.get("role"))
        # Fetch student profile using /api/students/{id}
        stud_id = prof_data.get("id")
        resp_stud = requests.get(f"http://127.0.0.1:8000/api/students/{stud_id}", headers=headers)
        print("Student Profile Status:", resp_stud.status_code)
        if resp_stud.status_code == 200:
            stud_data = resp_stud.json()
            print("Student profile Name:", stud_data.get("name"), "| Verification Status:", stud_data.get("verification_status"))
