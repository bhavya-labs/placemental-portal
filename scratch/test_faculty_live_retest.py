import sys, os
sys.path.insert(0, os.path.abspath('.'))
from fastapi.testclient import TestClient
from backend.app.main import app
import json

client = TestClient(app)

# Login as admin to set up an IT-inclusive drive for faculty.cse to manage
admin_res = client.post("/api/auth/login", json={"email": "admin@platform.edu", "password": "password123"})
admin_headers = {"Authorization": f"Bearer {admin_res.json()['access_token']}"}

# Login as faculty.cse
faculty_res = client.post("/api/auth/login", json={"email": "faculty.cse@platform.edu", "password": "password123"})
assert faculty_res.status_code == 200, f"Faculty login failed: {faculty_res.text}"
faculty_headers = {"Authorization": f"Bearer {faculty_res.json()['access_token']}"}

# Setup an IT-inclusive test drive
initial_drive = {
    "company_id": 2, # Microsoft
    "role": "Cloud DevOps Engineer",
    "package_lpa": 14.0,
    "location": "Hyderabad",
    "cgpa_cutoff": 7.0,
    "allowed_depts": "CSE,IT",
    "allowed_backlogs": 1,
    "bond_details": "None",
    "selection_process": "Technical Interview",
    "interview_date": "2026-10-20",
    "deadline": "2026-10-15",
    "status": "DRAFT",
    "job_id": "REPRO-DRIVE-01",
    "batch": "2026",
    "min_attendance": 75.0
}
create_res = client.post("/api/drives", json=initial_drive, headers=admin_headers)
assert create_res.status_code == 200
drive_id = create_res.json()["id"]

print(f"\n=======================================================")
print(f"LIVE FACULTY RE-TEST: DRIVE ID {drive_id}")
print(f"=======================================================")

try:
    # -------------------------------------------------------------------------
    # TEST 1: Edit basic fields (package_lpa, location, deadline) and save
    # -------------------------------------------------------------------------
    step1_payload = {
        **initial_drive,
        "package_lpa": 16.5,
        "location": "Bengaluru Tech Park",
        "deadline": "2026-10-18"
    }
    print("\n--- TEST 1: EDIT BASIC FIELDS ---")
    print("Request: PUT /api/drives/" + str(drive_id))
    print("Payload:", json.dumps({"package_lpa": 16.5, "location": "Bengaluru Tech Park", "deadline": "2026-10-18"}))
    
    put_res1 = client.put(f"/api/drives/{drive_id}", json=step1_payload, headers=faculty_headers)
    print(f"Response: HTTP {put_res1.status_code}")
    print("Response Body:", put_res1.json())
    assert put_res1.status_code == 200, f"Step 1 failed: {put_res1.text}"
    assert put_res1.json()["company_id"] == 2, "Company ID corrupted!"
    assert put_res1.json()["package_lpa"] == 16.5
    assert put_res1.json()["location"] == "Bengaluru Tech Park"
    assert put_res1.json()["deadline"] == "2026-10-18"

    # Re-fetch via GET /api/drives/{id}
    get_res1 = client.get(f"/api/drives/{drive_id}", headers=faculty_headers)
    print("GET status:", get_res1.status_code)
    print("GET body:", get_res1.json())
    get_data1 = get_res1.json()
    assert get_data1["company_id"] == 2, "Persisted company_id corrupted!"
    assert get_data1["package_lpa"] == 16.5, "package_lpa did not persist!"
    assert get_data1["location"] == "Bengaluru Tech Park", "location did not persist!"
    assert get_data1["deadline"] == "2026-10-18", "deadline did not persist!"
    print("[PASS] Test 1: Basic fields persisted correctly in database")

    # -------------------------------------------------------------------------
    # TEST 2: Lifecycle status change (DRAFT -> PUBLISHED)
    # -------------------------------------------------------------------------
    step2_payload = {
        **step1_payload,
        "status": "PUBLISHED"
    }
    print("\n--- TEST 2: LIFECYCLE STATUS TRANSITION (DRAFT -> PUBLISHED) ---")
    put_res2 = client.put(f"/api/drives/{drive_id}", json=step2_payload, headers=faculty_headers)
    print(f"Response: HTTP {put_res2.status_code}")
    print("Response Body:", put_res2.json())
    assert put_res2.status_code == 200, f"Step 2 failed: {put_res2.text}"
    assert put_res2.json()["status"] == "PUBLISHED"

    # Re-fetch via GET /api/drives/{id}
    get_res2 = client.get(f"/api/drives/{drive_id}", headers=faculty_headers)
    assert get_res2.json()["status"] == "PUBLISHED", "status did not persist!"
    print("[PASS] Test 2: Lifecycle transition to PUBLISHED persisted correctly")

    # -------------------------------------------------------------------------
    # TEST 3: Edit eligibility criteria (CGPA cutoff, allowed depts, backlogs, attendance)
    # -------------------------------------------------------------------------
    step3_payload = {
        **step2_payload,
        "cgpa_cutoff": 8.0,
        "allowed_depts": "IT,ECE",
        "allowed_backlogs": 0,
        "min_attendance": 80.0
    }
    print("\n--- TEST 3: EDIT ELIGIBILITY CRITERIA ---")
    put_res3 = client.put(f"/api/drives/{drive_id}", json=step3_payload, headers=faculty_headers)
    print(f"Response: HTTP {put_res3.status_code}")
    print("Response Body:", put_res3.json())
    assert put_res3.status_code == 200, f"Step 3 failed: {put_res3.text}"
    assert put_res3.json()["cgpa_cutoff"] == 8.0
    assert put_res3.json()["allowed_depts"] == "IT,ECE"
    assert put_res3.json()["allowed_backlogs"] == 0
    assert put_res3.json()["min_attendance"] == 80.0

    # Re-fetch via GET /api/drives/{id}
    get_res3 = client.get(f"/api/drives/{drive_id}", headers=faculty_headers)
    get_data3 = get_res3.json()
    assert get_data3["cgpa_cutoff"] == 8.0
    assert get_data3["allowed_depts"] == "IT,ECE"
    assert get_data3["allowed_backlogs"] == 0
    assert get_data3["min_attendance"] == 80.0
    print("[PASS] Test 3: Eligibility criteria persisted correctly in database")

finally:
    client.delete(f"/api/drives/{drive_id}", headers=admin_headers)
    print("\n[PASS] Cleaned up live re-test drive")
