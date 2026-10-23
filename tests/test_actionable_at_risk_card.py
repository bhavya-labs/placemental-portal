import pytest
from backend.app.models import User, Student, Department
from backend.app.auth import create_access_token

def test_at_risk_counts_identical_between_dashboard_and_student_details(client, db_session):
    """
    Ensure the count displayed on the dashboard card ('Students At Risk') exactly matches
    the count in summary and the number of students returned by the filtered list.
    Both must come from the same underlying backend filtering logic.
    """
    # Find a faculty member with an assigned department
    cse_faculty = db_session.query(User).filter(User.email == "faculty.cse@platform.edu").first()
    if not cse_faculty:
        cse_faculty = db_session.query(User).filter(User.role == "faculty").first()
    assert cse_faculty is not None, "Faculty user required for test"

    token = create_access_token(data={"sub": cse_faculty.email, "role": "faculty"})
    headers = {"Authorization": f"Bearer {token}"}
    dept_id = cse_faculty.faculty_profile.dept_id
    batch = "2026"

    # 1. Dashboard stats API
    dash_resp = client.get(f"/api/analytics/dashboard?dept_id={dept_id}&batch={batch}", headers=headers)
    assert dash_resp.status_code == 200, f"Dashboard stats failed: {dash_resp.text}"
    dash_data = dash_resp.json()
    dashboard_at_risk_count = dash_data["at_risk_count"]

    # 2. Department placement details summary API
    dept_resp = client.get(f"/api/students/department-placement-details?dept_id={dept_id}&batch={batch}", headers=headers)
    assert dept_resp.status_code == 200, f"Department placement details failed: {dept_resp.text}"
    dept_data = dept_resp.json()
    summary_at_risk_count = dept_data["summary"]["at_risk_students"]

    # Must be identical!
    assert dashboard_at_risk_count == summary_at_risk_count, (
        f"Mismatch between dashboard ({dashboard_at_risk_count}) and summary ({summary_at_risk_count})"
    )

    # 3. Filtered Department placement details table API (when status_filter="At Risk")
    filtered_resp = client.get(
        f"/api/students/department-placement-details?dept_id={dept_id}&batch={batch}&status_filter=At%20Risk&limit=200",
        headers=headers
    )
    assert filtered_resp.status_code == 200, f"Filtered table request failed: {filtered_resp.text}"
    filtered_data = filtered_resp.json()
    filtered_total = filtered_data["total"]
    students = filtered_data["items"]

    # Verify table count matches dashboard card count exactly
    assert filtered_total == dashboard_at_risk_count, (
        f"Filtered total ({filtered_total}) does not match dashboard count ({dashboard_at_risk_count})"
    )
    assert len(students) == dashboard_at_risk_count, (
        f"Returned items count ({len(students)}) does not match dashboard count ({dashboard_at_risk_count})"
    )

    # 4. Verify all returned students belong to "At Risk" category
    for s in students:
        assert s["status"] == "At Risk", f"Student {s['name']} has status {s['status']} instead of 'At Risk'"
        # Verify required student details are present
        assert "name" in s
        assert "roll_no" in s
        assert "branch" in s
        assert "section" in s
        assert "cgpa" in s
        assert "attendance" in s
        assert "placement_preparation_score" in s
        assert "status" in s
        assert "drives_applied_count" in s
        assert "interviews_attended_count" in s
        assert "selections_count" in s
        assert "active_applications_count" in s

def test_department_rbac_strictly_enforced_for_filtered_students(client, db_session):
    """
    Ensure a faculty member cannot view students from another department without permission,
    preventing unauthorized data exposure.
    """
    cse_faculty = db_session.query(User).filter(User.email == "faculty.cse@platform.edu").first()
    it_dept = db_session.query(Department).filter(Department.code == "IT").first()
    assert cse_faculty is not None and it_dept is not None

    token = create_access_token(data={"sub": cse_faculty.email, "role": "faculty"})
    headers = {"Authorization": f"Bearer {token}"}

    # Requesting IT department without elevated grant must return 403 Forbidden
    resp = client.get(
        f"/api/students/department-placement-details?dept_id={it_dept.id}&status_filter=At%20Risk",
        headers=headers
    )
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]

def test_all_students_directory_status_filter_normalized(client, db_session):
    """
    Ensure the general student directory (/api/students) also correctly filters by 'At Risk'
    and matches the count, identity, and attributes of the database records.
    """
    cse_faculty = db_session.query(User).filter(User.email == "faculty.cse@platform.edu").first()
    token = create_access_token(data={"sub": cse_faculty.email, "role": "faculty"})
    headers = {"Authorization": f"Bearer {token}"}
    dept_id = cse_faculty.faculty_profile.dept_id

    resp = client.get(
        f"/api/students?dept_id={dept_id}&batch=2026&status_filter=At%20Risk&limit=200",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]
    expected_students = db_session.query(Student).filter(
        Student.dept_id == dept_id,
        Student.batch == "2026",
        Student.status == "At Risk"
    ).all()
    assert len(items) == len(expected_students)
    assert len(expected_students) > 0

    expected_ids = {s.id for s in expected_students}
    returned_ids = {item["id"] for item in items}
    assert returned_ids == expected_ids, "Returned student IDs do not match database records"

    for item in items:
        assert item["status"] == "At Risk", f"Student {item.get('name')} does not have status 'At Risk'"
        assert item["dept_id"] == dept_id
        assert item["batch"] == "2026"
        assert "name" in item
        assert "email" in item
        assert "cgpa" in item
        assert "attendance" in item
        assert "backlogs" in item
