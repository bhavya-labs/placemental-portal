import sys, os
sys.path.insert(0, os.path.abspath('.'))
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

res = client.post("/api/auth/login", json={"email": "admin@platform.edu", "password": "password123"})
assert res.status_code == 200, f"Login failed: {res.text}"
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test GET /api/drives
drives_res = client.get("/api/drives", headers=headers)
assert drives_res.status_code == 200, f"GET /api/drives failed: {drives_res.text}"
drives = drives_res.json()
print(f"Total drives fetched: {len(drives)}")
for d in drives:
    assert "company_id" in d, f"Drive {d['id']} missing company_id!"
    assert d["company_id"] is not None and d["company_id"] > 0, f"Drive {d['id']} has invalid company_id: {d.get('company_id')}"
print("[PASS] All drives in GET /api/drives contain valid company_id")

# Test GET /api/drives/{id} for sample drives
for d in drives[:5]:
    detail_res = client.get(f"/api/drives/{d['id']}", headers=headers)
    assert detail_res.status_code == 200, f"GET /api/drives/{d['id']} failed: {detail_res.text}"
    detail = detail_res.json()
    assert "company_id" in detail, f"Drive detail {d['id']} missing company_id!"
    assert detail["company_id"] == d["company_id"], f"company_id mismatch for drive {d['id']}!"
print("[PASS] GET /api/drives/{id} correctly returns matching company_id")
