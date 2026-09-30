import requests

BASE_URL = 'http://127.0.0.1:8000'

def test_full_flow():
    # 1. Login as CSE Faculty
    login_res = requests.post(f'{BASE_URL}/api/auth/login', json={'email': 'faculty.cse@platform.edu', 'password': 'password123'})
    assert login_res.status_code == 200, f'Login failed: {login_res.text}'
    token = login_res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('[PASS] Login as CSE Faculty successful')

    # 2. Get Faculty Dashboard Stats
    dash_res = requests.get(f'{BASE_URL}/api/analytics/dashboard?dept_id=1&batch=2026', headers=headers)
    assert dash_res.status_code == 200, f'Dashboard failed: {dash_res.text}'
    dash_stats = dash_res.json()
    total_students = dash_stats["total_students"]
    placed_students = dash_stats["placed_students"]
    at_risk_count = dash_stats["at_risk_count"]
    print(f'[PASS] Dashboard loaded: Total Students={total_students}, Placed={placed_students}, At Risk={at_risk_count}')

    # 3. Simulate clicking 'Students At Risk' card -> /student-tracker?status=At%20Risk&batch=2026&dept_id=1
    dept_details_res = requests.get(f'{BASE_URL}/api/students/department-placement-details?dept_id=1&batch=2026&status_filter=At%20Risk&limit=100', headers=headers)
    assert dept_details_res.status_code == 200, f'Department placement details failed: {dept_details_res.text}'
    dept_data = dept_details_res.json()
    print(f'[PASS] Department placement details loaded: Total matching={dept_data["total"]}, Summary At Risk={dept_data["summary"]["at_risk_students"]}')

    assert dept_data['total'] == at_risk_count, f"Count mismatch: table={dept_data['total']} vs dash={at_risk_count}"
    assert dept_data['summary']['at_risk_students'] == at_risk_count, f"Count mismatch: summary={dept_data['summary']['at_risk_students']} vs dash={at_risk_count}"
    print(f'[PASS] Exact count consistency verified: Dashboard At Risk = {at_risk_count}, Filtered Table = {dept_data["total"]}, Summary Card = {dept_data["summary"]["at_risk_students"]}')

    # 4. Check student record fields
    first_student = dept_data['items'][0]
    required_fields = ['roll_no', 'name', 'branch', 'section', 'cgpa', 'attendance', 'placement_preparation_score', 'status', 'drives_applied_count', 'selections_count', 'active_applications_count']
    for rf in required_fields:
        assert rf in first_student, f'Missing field: {rf}'
    print(f'[PASS] Student fields verified: {first_student["name"]} (Roll: {first_student["roll_no"]}, Branch: {first_student["branch"]}-{first_student["section"]}, CGPA: {first_student["cgpa"]}, Status: {first_student["status"]}, Prep Score: {first_student["placement_preparation_score"]})')

    # 5. Check RBAC enforcement (attempting unauthorized IT dept)
    rbac_res = requests.get(f'{BASE_URL}/api/students/department-placement-details?dept_id=2&batch=2026&status_filter=At%20Risk', headers=headers)
    assert rbac_res.status_code == 403, f'RBAC failed: Expected 403, got {rbac_res.status_code}'
    print(f'[PASS] RBAC enforced: Unauthorized department query returned {rbac_res.status_code} Forbidden')

    # 6. Check Placed card filter -> status=Placed
    placed_res = requests.get(f'{BASE_URL}/api/students/department-placement-details?dept_id=1&batch=2026&status_filter=Placed&limit=100', headers=headers)
    assert placed_res.status_code == 200
    placed_data = placed_res.json()
    assert placed_data['total'] == placed_students == 12
    print(f'[PASS] Actionable Placed Card also verified: Dashboard Placed = {placed_students}, Filtered List = {placed_data["total"]}')

    # 7. Check directory endpoint filter -> status=At Risk
    dir_res = requests.get(f'{BASE_URL}/api/students?dept_id=1&batch=2026&status_filter=At%20Risk&limit=100', headers=headers)
    assert dir_res.status_code == 200
    dir_data = dir_res.json()
    assert dir_data['total'] == at_risk_count == 44
    print(f'[PASS] Student Directory also returns exactly {dir_data["total"]} matching At Risk students')

    print('\n========================================')
    print('ALL VERIFICATION CHECKS PASSED!')
    print('========================================')

if __name__ == '__main__':
    test_full_flow()
