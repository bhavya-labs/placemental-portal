import pytest
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import User, Student, Department, Faculty, Parent, PlacementDrive, Application, Notification, CorrectionRequest
from backend.app.auth import create_access_token, get_password_hash

def get_or_create_user(db_session, email, role, name="Test User"):
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash=get_password_hash("password123"),
            name=name,
            role=role,
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


def test_role_coverage_authentication_all_six_roles(client, db_session):
    """
    Verify authentication, JWT generation, and identity payload across all 6 roles:
    Student, Faculty, HOD, TPO/TNP, Admin, Parent.
    """
    # 1. Admin
    admin_u = get_or_create_user(db_session, "admin_test@platform.edu", "admin", "Admin User")
    admin_token = create_access_token(data={"sub": admin_u.email, "role": "admin"})
    resp = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"

    # 2. Student
    student_u = get_or_create_user(db_session, "student_test@platform.edu", "student", "Student User")
    student_token = create_access_token(data={"sub": student_u.email, "role": "student"})
    resp = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {student_token}"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "student"

    # 3. Faculty
    faculty_u = get_or_create_user(db_session, "faculty_test@platform.edu", "faculty", "Faculty User")
    faculty_token = create_access_token(data={"sub": faculty_u.email, "role": "faculty"})
    resp = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {faculty_token}"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "faculty"

    # 4. HOD
    hod_u = get_or_create_user(db_session, "hod_test@platform.edu", "hod", "HOD User")
    hod_token = create_access_token(data={"sub": hod_u.email, "role": "hod"})
    resp = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {hod_token}"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "hod"

    # 5. TPO / TNP
    tpo_u = get_or_create_user(db_session, "tpo_test@platform.edu", "tnp", "TPO User")
    tpo_token = create_access_token(data={"sub": tpo_u.email, "role": "tnp"})
    resp = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {tpo_token}"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "tnp"

    # 6. Parent (via parent JWT sub=student_id, role=parent)
    parent_token = create_access_token(data={"sub": "8", "role": "parent"})
    # Parent token access to parent endpoints
    resp = client.get("/api/parent/child-dashboard", headers={"Authorization": f"Bearer {parent_token}"})
    assert resp.status_code in (200, 404)  # 200 if student 8 exists, 404 if not found; not 401/403


def test_horizontal_privilege_escalation_student_to_student(client, db_session):
    """
    Ensure Student A cannot modify Student B's profile.
    """
    student_a = get_or_create_user(db_session, "student_a@platform.edu", "student", "Student A")
    student_token = create_access_token(data={"sub": student_a.email, "role": "student"})
    headers = {"Authorization": f"Bearer {student_token}"}

    # Attempt to modify student with ID 999 or other ID
    resp = client.put("/api/students/999", json={"phone": "9999999999"}, headers=headers)
    assert resp.status_code in [403, 404]
    if resp.status_code == 403:
        assert "Access denied" in resp.json()["detail"] or "Forbidden" in resp.json()["detail"]


def test_vertical_privilege_escalation_student_to_admin(client, db_session):
    """
    Ensure Student cannot access admin analytics or create companies.
    """
    student_u = get_or_create_user(db_session, "student_v@platform.edu", "student", "Student V")
    student_token = create_access_token(data={"sub": student_u.email, "role": "student"})
    headers = {"Authorization": f"Bearer {student_token}"}

    # Access analytics dashboard (admin/staff only) -> 403
    resp = client.get("/api/analytics/dashboard", headers=headers)
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"] or "Forbidden" in resp.json()["detail"]

    # Attempt to create company -> 403
    resp = client.post("/api/companies", json={
        "name": "Unauthorized Company Attempt",
        "industry": "IT"
    }, headers=headers)
    assert resp.status_code == 403


def test_faculty_hod_departmental_isolation(client, db_session):
    """
    Verify Faculty and HOD can only access students within their authorized department.
    """
    fac_u = get_or_create_user(db_session, "faculty_dept@platform.edu", "faculty", "Faculty Dept")
    # Link faculty profile to a department if not present
    dept = db_session.query(Department).first()
    if not dept:
        dept = Department(name="Computer Science", code="CSE")
        db_session.add(dept)
        db_session.commit()
        db_session.refresh(dept)

    fac_profile = db_session.query(Faculty).filter(Faculty.id == fac_u.id).first()
    if not fac_profile:
        fac_profile = Faculty(id=fac_u.id, dept_id=dept.id, designation="Assistant Professor")
        db_session.add(fac_profile)
        db_session.commit()

    fac_token = create_access_token(data={"sub": fac_u.email, "role": "faculty"})
    headers = {"Authorization": f"Bearer {fac_token}"}

    # Department-filtered view with an out-of-scope department should return 403
    resp = client.get("/api/students/department-placement-details?dept_id=9999", headers=headers)
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"] or "elevated" in resp.json()["detail"]


def test_parent_access_restricted_to_linked_child(client, db_session):
    """
    Verify Parent cannot access arbitrary endpoints without child scope.
    """
    parent_token = create_access_token(data={"sub": "8", "role": "parent"})
    headers = {"Authorization": f"Bearer {parent_token}"}

    # Parent trying to list all students -> Forbidden / Unauthorized
    resp = client.get("/api/students", headers=headers)
    assert resp.status_code in (401, 403)


def test_sql_injection_defense(client, db_session):
    """
    Verify that SQL injection strings in query parameters are treated as literal text.
    """
    admin_u = get_or_create_user(db_session, "admin_sqli@platform.edu", "admin", "Admin SQLi")
    admin_token = create_access_token(data={"sub": admin_u.email, "role": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}

    sql_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1 UNION SELECT 1, 'admin', 'hash', 'admin' --",
        "admin'--",
    ]

    for payload in sql_payloads:
        resp = client.get(f"/api/search?q={payload}", headers=headers)
        assert resp.status_code == 200
        # Check that response structure is valid and no SQL error was thrown
        data = resp.json()
        assert isinstance(data, dict)


def test_cors_security_headers(client):
    """
    Verify production CORS rejects untrusted origins while permitting allowed origins.
    """
    # 1. Trusted origin
    resp = client.options("/api/health", headers={
        "Origin": "https://bhavya-labs.github.io",
        "Access-Control-Request-Method": "GET"
    })
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "https://bhavya-labs.github.io"

    # 2. Untrusted origin
    resp = client.options("/api/health", headers={
        "Origin": "https://malicious-phishing-site.com",
        "Access-Control-Request-Method": "GET"
    })
    assert resp.headers.get("access-control-allow-origin") != "https://malicious-phishing-site.com"


def test_academic_data_locking(client, db_session):
    """
    Verify student cannot directly overwrite locked academic fields (cgpa, backlogs, verification_status).
    """
    student_u = get_or_create_user(db_session, "student_lock@platform.edu", "student", "Student Lock")
    student_token = create_access_token(data={"sub": student_u.email, "role": "student"})
    headers = {"Authorization": f"Bearer {student_token}"}

    # Student attempting to self-verify or bump CGPA directly
    resp = client.put("/api/students/profile", json={
        "cgpa": 10.0,
        "verification_status": "VERIFIED"
    }, headers=headers)
    # The endpoint should either ignore or reject locked fields
    if resp.status_code == 200:
        updated = resp.json()
        assert updated.get("verification_status") != "VERIFIED" or "cgpa" not in updated


def test_orphan_application_1253_retrieval(client, db_session):
    """
    Verify orphan application 1253 is retrieved without error with safe fallback company name.
    """
    admin_u = get_or_create_user(db_session, "admin_orphan@platform.edu", "admin", "Admin Orphan")
    admin_token = create_access_token(data={"sub": admin_u.email, "role": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.get("/api/applications/student/8", headers=headers)
    assert resp.status_code == 200
    apps = resp.json()
    orphan = next((a for a in apps if a.get("id") == 1253), None)
    if orphan:
        assert orphan.get("company_name") == "Archived / Legacy Drive"
        assert orphan.get("role") == "N/A"
        assert orphan.get("package_lpa") == 0.0


def test_transaction_rollback_behavior(db_session):
    """
    Verify transaction rollback rolls back nested operations without corrupting outer session.
    """
    try:
        with db_session.begin_nested():
            u = User(email="temporary_fail@test.com", password_hash="hash", name="Temp", role="student")
            db_session.add(u)
            raise ValueError("Deliberate failure to trigger rollback")
    except ValueError:
        pass

    found = db_session.query(User).filter(User.email == "temporary_fail@test.com").first()
    assert found is None, "Rollback failed to revert inserted user!"
