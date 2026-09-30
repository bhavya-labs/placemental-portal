from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Company, PlacementDrive, Student
from backend.app.auth import create_access_token
import json

client = TestClient(app, raise_server_exceptions=False)
faculty_token = create_access_token(data={"sub": "faculty.cse@platform.edu", "role": "faculty"})
admin_token = create_access_token(data={"sub": "admin@platform.edu", "role": "admin"})

print("==================================================")
print("TEST 1: GET /api/analytics/dashboard (FACULTY)")
print("==================================================")
for label, headers in [("Faculty", {"Authorization": f"Bearer {faculty_token}"}), ("Admin", {"Authorization": f"Bearer {admin_token}"})]:
    print(f"\n--- Testing as {label} ---")
    # Test without filters
    resp = client.get("/api/analytics/dashboard", headers=headers)
    print(f"Status (no filters): {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print("KPIs:", {k: data.get(k) for k in ["total_students", "placed_students", "placement_percentage", "highest_package", "average_package", "median_package", "at_risk_count"]})
        print("Branch hiring count:", len(data.get("branch_hiring", [])))
        print("Monthly trend count:", len(data.get("monthly_trend", [])))
        print("Gender stats:", data.get("gender_stats"))
        print("Funnel data:", data.get("funnel_data"))
    else:
        print("Response:", resp.text)

    # Test WITH dept_id filter (e.g. dept_id=1 for CSE)
    resp_dept = client.get("/api/analytics/dashboard?dept_id=1", headers=headers)
    print(f"Status (dept_id=1): {resp_dept.status_code}")
    if resp_dept.status_code != 200:
        print("Error with dept_id=1:", resp_dept.text)
    else:
        d = resp_dept.json()
        print("With dept_id=1 - Total:", d.get("total_students"), "Placed:", d.get("placed_students"), "Branch hiring:", d.get("branch_hiring"))

print("\n==================================================")
print("TEST 2: GET /api/analytics/company/{company_id}")
print("==================================================")
db = SessionLocal()
comps = db.query(Company).all()
print(f"Total companies in DB: {len(comps)}")
for c in comps[:3]:
    print(f"Company ID {c.id}: {c.name}")
db.close()

if comps:
    cid = comps[0].id
    for label, headers in [("Faculty", {"Authorization": f"Bearer {faculty_token}"}), ("Admin", {"Authorization": f"Bearer {admin_token}"})]:
        print(f"\n--- Testing company {cid} as {label} ---")
        resp_comp = client.get(f"/api/analytics/company/{cid}", headers=headers)
        print(f"Status: {resp_comp.status_code}")
        print("Body:", resp_comp.text)

# Also test raising exceptions to get tracebacks if any 500
print("\n--- Checking for unhandled exceptions ---")
client_raise = TestClient(app, raise_server_exceptions=True)
try:
    client_raise.get("/api/analytics/dashboard", headers={"Authorization": f"Bearer {faculty_token}"})
    print("Dashboard: No unhandled exception.")
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    if comps:
        client_raise.get(f"/api/analytics/company/{comps[0].id}", headers={"Authorization": f"Bearer {faculty_token}"})
        print("Company Analytics: No unhandled exception.")
except Exception as e:
    import traceback
    traceback.print_exc()
