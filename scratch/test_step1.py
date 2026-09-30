import requests

BASE = 'http://127.0.0.1:8000'

# Login as admin to get token
res = requests.post(f'{BASE}/api/auth/login', json={'email': 'admin@platform.edu', 'password': 'password123'})
assert res.status_code == 200, f'Login failed: {res.text}'
token = res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test GET /api/drives
r = requests.get(f'{BASE}/api/drives', headers=headers)
assert r.status_code == 200, f'GET /api/drives failed: {r.status_code}'
drives = r.json()
print(f'Retrieved {len(drives)} drives from /api/drives')
assert len(drives) > 0

missing_company_id = [d['id'] for d in drives if 'company_id' not in d or d['company_id'] is None]
print(f'Drives missing company_id in /api/drives: {missing_company_id}')
assert len(missing_company_id) == 0, 'Found drives missing company_id'

# Check drive 20 specifically
d20 = next((d for d in drives if d['id'] == 20), None)
if d20:
    print(f"Drive 20 in list: company_id={d20.get('company_id')}, company_name={d20.get('company_name')}")
    assert d20.get('company_id') == 21

# Test GET /api/drives/20
r_detail = requests.get(f'{BASE}/api/drives/20', headers=headers)
assert r_detail.status_code == 200, f'GET /api/drives/20 failed: {r_detail.status_code}'
detail20 = r_detail.json()
print(f"Drive 20 details: company_id={detail20.get('company_id')}, company_name={detail20.get('company_name')}, applied_list={len(detail20.get('applied_list', []))}")
assert detail20.get('company_id') == 21
assert 'applied_list' in detail20

print('ALL STEP 1 API CHECKS PASSED!')
