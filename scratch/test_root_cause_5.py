import sys, os
sys.path.insert(0, os.path.abspath('.'))
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import PlacementDrive, Company

client = TestClient(app)

# Login as admin to set up test drives
admin_res = client.post("/api/auth/login", json={"email": "admin@platform.edu", "password": "password123"})
assert admin_res.status_code == 200
admin_headers = {"Authorization": f"Bearer {admin_res.json()['access_token']}"}

# Login as faculty.cse
faculty_res = client.post("/api/auth/login", json={"email": "faculty.cse@platform.edu", "password": "password123"})
assert faculty_res.status_code == 200
faculty_headers = {"Authorization": f"Bearer {faculty_res.json()['access_token']}"}

# Create a CSE-only drive
cse_only_payload = {
    "company_id": 1,
    "role": "CSE Exclusive Role",
    "package_lpa": 12.0,
    "location": "Hyderabad",
    "cgpa_cutoff": 7.0,
    "allowed_depts": "CSE",
    "allowed_backlogs": 0,
    "bond_details": "None",
    "selection_process": "Interview",
    "interview_date": "2026-10-10",
    "deadline": "2026-10-05",
    "status": "PUBLISHED",
    "job_id": "TEST-CSE-ONLY-01",
    "batch": "2026",
    "min_attendance": 75.0
}
cse_res = client.post("/api/drives", json=cse_only_payload, headers=admin_headers)
assert cse_res.status_code == 200
cse_drive_id = cse_res.json()["id"]

# Create an IT-inclusive drive
it_inclusive_payload = {
    "company_id": 1,
    "role": "IT Inclusive Role",
    "package_lpa": 12.0,
    "location": "Hyderabad",
    "cgpa_cutoff": 7.0,
    "allowed_depts": "CSE,IT",
    "allowed_backlogs": 0,
    "bond_details": "None",
    "selection_process": "Interview",
    "interview_date": "2026-10-10",
    "deadline": "2026-10-05",
    "status": "PUBLISHED",
    "job_id": "TEST-IT-INCL-01",
    "batch": "2026",
    "min_attendance": 75.0
}
it_res = client.post("/api/drives", json=it_inclusive_payload, headers=admin_headers)
assert it_res.status_code == 200
it_drive_id = it_res.json()["id"]

try:
    # 1. Attempt to edit CSE-only drive as faculty.cse (scoped to IT)
    edit_cse_payload = {**cse_only_payload, "location": "Bengaluru"}
    res_edit_cse = client.put(f"/api/drives/{cse_drive_id}", json=edit_cse_payload, headers=faculty_headers)
    print("Edit CSE-only drive response status:", res_edit_cse.status_code)
    print("Response detail:", res_edit_cse.text)
    assert res_edit_cse.status_code == 403, f"Expected 403, got {res_edit_cse.status_code}"
    print("[PASS] faculty.cse CANNOT edit CSE-only drive (HTTP 403 Forbidden)")

    # 2. Attempt to edit IT-inclusive drive as faculty.cse (scoped to IT)
    edit_it_payload = {**it_inclusive_payload, "location": "Bengaluru"}
    res_edit_it = client.put(f"/api/drives/{it_drive_id}", json=edit_it_payload, headers=faculty_headers)
    print("Edit IT-inclusive drive response status:", res_edit_it.status_code)
    assert res_edit_it.status_code == 200, f"Expected 200, got {res_edit_it.status_code}: {res_edit_it.text}"
    print("[PASS] faculty.cse CAN edit IT-inclusive drive (HTTP 200 OK)")

finally:
    # Cleanup test drives
    client.delete(f"/api/drives/{cse_drive_id}", headers=admin_headers)
    client.delete(f"/api/drives/{it_drive_id}", headers=admin_headers)
    print("[PASS] Cleaned up test drives")
