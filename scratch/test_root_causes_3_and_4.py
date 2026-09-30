import sys, os
sys.path.insert(0, os.path.abspath('.'))
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

admin_res = client.post("/api/auth/login", json={"email": "admin@platform.edu", "password": "password123"})
assert admin_res.status_code == 200
admin_headers = {"Authorization": f"Bearer {admin_res.json()['access_token']}"}

# Create drive in DRAFT
create_payload = {
    "company_id": 1,
    "role": "State Machine Test Engineer",
    "package_lpa": 10.0,
    "location": "Hyderabad",
    "cgpa_cutoff": 7.0,
    "allowed_depts": "CSE,IT",
    "allowed_backlogs": 0,
    "bond_details": "None",
    "selection_process": "Interview",
    "interview_date": "2026-10-15",
    "deadline": "2026-10-10",
    "status": "DRAFT",
    "job_id": "TEST-SM-01",
    "batch": "2026",
    "min_attendance": 75.0
}
res_create = client.post("/api/drives", json=create_payload, headers=admin_headers)
assert res_create.status_code == 200
drive_id = res_create.json()["id"]

try:
    # Test Root Cause 3 & 4: Transition from DRAFT to Active and verify non-empty response
    edit_payload = {
        **create_payload,
        "package_lpa": 12.5,
        "location": "Bengaluru",
        "status": "Active"
    }
    res_update = client.put(f"/api/drives/{drive_id}", json=edit_payload, headers=admin_headers)
    assert res_update.status_code == 200, f"Update failed: {res_update.text}"
    data = res_update.json()
    print("PUT /api/drives response payload keys:", list(data.keys()))
    assert len(data) > 0, "Response is empty {}!"
    assert data["id"] == drive_id
    assert data["company_id"] == 1
    assert data["package_lpa"] == 12.5
    assert data["location"] == "Bengaluru"
    assert data["status"] == "Active"
    print("[PASS] Root Cause 4: Response is fully populated and adheres to response_model (NOT empty {})")
    print("[PASS] Root Cause 3: Transition from DRAFT to 'Active' succeeded")

    # Verify persistence via GET /api/drives/{id}
    res_get = client.get(f"/api/drives/{drive_id}", headers=admin_headers)
    assert res_get.status_code == 200
    get_data = res_get.json()
    assert get_data["package_lpa"] == 12.5
    assert get_data["location"] == "Bengaluru"
    assert get_data["status"] == "Active"
    print("[PASS] Verified changes persisted in database via GET /api/drives/{id}")

    # Test Transition from Active to COMPLETED
    completed_payload = {**edit_payload, "status": "COMPLETED"}
    res_completed = client.put(f"/api/drives/{drive_id}", json=completed_payload, headers=admin_headers)
    assert res_completed.status_code == 200
    assert res_completed.json()["status"] == "COMPLETED"
    print("[PASS] Root Cause 3: Transition from 'Active' to 'COMPLETED' succeeded")

finally:
    client.delete(f"/api/drives/{drive_id}", headers=admin_headers)
    print("[PASS] Cleaned up test drive")
