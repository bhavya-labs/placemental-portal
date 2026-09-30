import requests

BASE = 'http://127.0.0.1:8000'

# 1. Login as faculty.cse@platform.edu
res_f = requests.post(f'{BASE}/api/auth/login', json={'email': 'faculty.cse@platform.edu', 'password': 'password123'})
assert res_f.status_code == 200, f'Faculty login failed: {res_f.text}'
f_token = res_f.json()['access_token']
f_headers = {'Authorization': f'Bearer {f_token}'}

# 2. Login as admin@platform.edu to inspect drive details and verify baseline
res_a = requests.post(f'{BASE}/api/auth/login', json={'email': 'admin@platform.edu', 'password': 'password123'})
assert res_a.status_code == 200, f'Admin login failed: {res_a.text}'
a_token = res_a.json()['access_token']
a_headers = {'Authorization': f'Bearer {a_token}'}

# Get CSE-only Drive (Drive 26)
d26 = requests.get(f'{BASE}/api/drives/26', headers=a_headers).json()
print(f"Drive 26: role='{d26['role']}', allowed_depts='{d26['allowed_depts']}'")
assert 'IT' not in d26['allowed_depts'].split(',')

# Test: faculty.cse CANNOT edit Drive 26 (CSE-only) -> must return 403
payload26 = dict(d26)
payload26['package_lpa'] = 14.0
res_put26 = requests.put(f'{BASE}/api/drives/26', json=payload26, headers=f_headers)
print(f"faculty.cse editing CSE-only drive 26: status={res_put26.status_code}, body={res_put26.text}")
assert res_put26.status_code == 403, f"Expected 403, got {res_put26.status_code}: {res_put26.text}"
assert "Access denied" in res_put26.text

# Get IT-inclusive Drive (Drive 22)
d22 = requests.get(f'{BASE}/api/drives/22', headers=a_headers).json()
print(f"Drive 22: role='{d22['role']}', allowed_depts='{d22['allowed_depts']}'")
assert 'IT' in d22['allowed_depts'].split(',')

# Test: faculty.cse CAN edit Drive 22 (IT-inclusive) -> must return 200
payload22 = dict(d22)
payload22['package_lpa'] = 7.5
res_put22 = requests.put(f'{BASE}/api/drives/22', json=payload22, headers=f_headers)
print(f"faculty.cse editing IT-inclusive drive 22: status={res_put22.status_code}")
assert res_put22.status_code == 200, f"Expected 200, got {res_put22.status_code}: {res_put22.text}"

# Test: admin (scope ALL) CAN edit Drive 26 (CSE-only) -> must return 200
res_admin_put = requests.put(f'{BASE}/api/drives/26', json=payload26, headers=a_headers)
print(f"admin editing CSE-only drive 26: status={res_admin_put.status_code}")
assert res_admin_put.status_code == 200

print("\nALL STEP 2 RBAC ENFORCEMENT CHECKS PASSED!")
