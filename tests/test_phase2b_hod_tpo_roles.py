"""
Isolated Integration and Authorization Tests for AP-CPIP Phase 2C.
Verifies HOD, Faculty, and TNP role boundaries, profile serialization,
account provisioning rules, transaction rollback safety, and system permission isolation.

All tests operate against the isolated local test SQLite database.
No connection to production database is used.
"""

import pytest
from datetime import datetime, date, timedelta
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models import (
    User, Student, Department, Faculty, Company, PlacementDrive, Parent, Permission
)
from backend.app.auth import create_access_token, get_password_hash


@pytest.fixture(scope="module")
def role_test_env(client: TestClient):
    """
    Sets up isolated test entities for HOD, Faculty, TNP, and departmental students.
    """
    from backend.app.database import SessionLocal
    db: Session = SessionLocal()

    # 1. Ensure departments exist
    dept_cse = db.query(Department).filter(Department.code == "CSE").first()
    if not dept_cse:
        dept_cse = Department(name="Computer Science & Engineering", code="CSE")
        db.add(dept_cse)
        db.flush()

    dept_ece = db.query(Department).filter(Department.code == "ECE").first()
    if not dept_ece:
        dept_ece = Department(name="Electronics & Communication Engineering", code="ECE")
        db.add(dept_ece)
        db.flush()

    pwd_hash = get_password_hash("password123")

    # 2. HOD User (CSE)
    hod_user = db.query(User).filter(User.email == "test_hod_cse@test.edu").first()
    if not hod_user:
        hod_user = User(
            email="test_hod_cse@test.edu",
            name="Dr. CSE HOD",
            role="hod",
            password_hash=pwd_hash
        )
        db.add(hod_user)
        db.flush()

    hod_faculty = db.query(Faculty).filter(Faculty.id == hod_user.id).first()
    if not hod_faculty:
        hod_faculty = Faculty(
            id=hod_user.id,
            dept_id=dept_cse.id,
            designation="Head of Department"
        )
        db.add(hod_faculty)
        db.flush()

    # 3. Faculty User (CSE)
    faculty_user = db.query(User).filter(User.email == "test_fac_cse@test.edu").first()
    if not faculty_user:
        faculty_user = User(
            email="test_fac_cse@test.edu",
            name="Prof. CSE Faculty",
            role="faculty",
            password_hash=pwd_hash
        )
        db.add(faculty_user)
        db.flush()

    faculty_profile = db.query(Faculty).filter(Faculty.id == faculty_user.id).first()
    if not faculty_profile:
        faculty_profile = Faculty(
            id=faculty_user.id,
            dept_id=dept_cse.id,
            designation="Assistant Professor"
        )
        db.add(faculty_profile)
        db.flush()

    # 4. TNP User (Global Placement Officer)
    tnp_user = db.query(User).filter(User.email == "test_tnp_officer@test.edu").first()
    if not tnp_user:
        tnp_user = User(
            email="test_tnp_officer@test.edu",
            name="TNP Officer",
            role="tnp",
            password_hash=pwd_hash
        )
        db.add(tnp_user)
        db.flush()

    # 5. Student in CSE (Dept CSE)
    student_cse_user = db.query(User).filter(User.email == "test_student_cse@test.edu").first()
    if not student_cse_user:
        student_cse_user = User(
            email="test_student_cse@test.edu",
            name="CSE Student",
            role="student",
            password_hash=pwd_hash
        )
        db.add(student_cse_user)
        db.flush()

    student_cse = db.query(Student).filter(Student.id == student_cse_user.id).first()
    if not student_cse:
        student_cse = Student(
            id=student_cse_user.id,
            dept_id=dept_cse.id,
            gender="Male",
            batch="2026",
            cgpa=8.5,
            attendance=85.0,
            backlogs=0,
            verification_status="UNVERIFIED"
        )
        db.add(student_cse)
        db.flush()

    # 6. Student in ECE (Dept ECE)
    student_ece_user = db.query(User).filter(User.email == "test_student_ece@test.edu").first()
    if not student_ece_user:
        student_ece_user = User(
            email="test_student_ece@test.edu",
            name="ECE Student",
            role="student",
            password_hash=pwd_hash
        )
        db.add(student_ece_user)
        db.flush()

    student_ece = db.query(Student).filter(Student.id == student_ece_user.id).first()
    if not student_ece:
        student_ece = Student(
            id=student_ece_user.id,
            dept_id=dept_ece.id,
            gender="Female",
            batch="2026",
            cgpa=9.0,
            attendance=90.0,
            backlogs=0,
            verification_status="UNVERIFIED"
        )
        db.add(student_ece)
        db.flush()

    db.commit()

    env_data = {
        "dept_cse_id": dept_cse.id,
        "dept_cse_code": dept_cse.code,
        "dept_cse_name": dept_cse.name,
        "dept_ece_id": dept_ece.id,
        "dept_ece_code": dept_ece.code,
        "dept_ece_name": dept_ece.name,
        "hod_id": hod_user.id,
        "hod_token": create_access_token({"sub": hod_user.email, "role": "hod"}),
        "faculty_id": faculty_user.id,
        "faculty_token": create_access_token({"sub": faculty_user.email, "role": "faculty"}),
        "tnp_id": tnp_user.id,
        "tnp_token": create_access_token({"sub": tnp_user.email, "role": "tnp"}),
        "student_cse_id": student_cse.id,
        "student_ece_id": student_ece.id,
    }
    db.close()
    return env_data


def test_01_hod_profile_serialization_includes_faculty_profile(client: TestClient, role_test_env):
    """
    1. HOD profile serialization includes `faculty_profile` with department details.
    """
    token = role_test_env["hod_token"]
    response = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["role"] == "hod"
    assert "faculty_profile" in data
    fp = data["faculty_profile"]
    assert fp is not None
    assert fp["dept_id"] == role_test_env["dept_cse_id"]
    assert fp["dept_code"] == role_test_env["dept_cse_code"]
    assert fp["dept_name"] == role_test_env["dept_cse_name"]
    assert fp["designation"] == "Head of Department"


def test_02_hod_profile_returns_correct_department(client: TestClient, role_test_env):
    """
    2. HOD profile returns the correct department assigned to the HOD.
    """
    token = role_test_env["hod_token"]
    response = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["faculty_profile"]["dept_id"] == role_test_env["dept_cse_id"]
    assert data["faculty_profile"]["dept_code"] == "CSE"


def test_03_hod_cannot_access_students_outside_department(client: TestClient, role_test_env):
    """
    3. HOD cannot access students outside their department (Dept ECE vs HOD CSE).
    """
    token = role_test_env["hod_token"]
    # Access student inside department (CSE) -> 200
    res_in = client.get(f"/api/students/{role_test_env['student_cse_id']}", headers={"Authorization": f"Bearer {token}"})
    assert res_in.status_code == 200, f"Expected 200 for student in department: {res_in.text}"

    # Access student outside department (ECE) -> 403
    res_out = client.get(f"/api/students/{role_test_env['student_ece_id']}", headers={"Authorization": f"Bearer {token}"})
    assert res_out.status_code == 403, f"Expected 403 for student outside department: {res_out.text}"


def test_04_hod_cannot_verify_student_outside_department(client: TestClient, role_test_env):
    """
    4. HOD cannot verify student outside their department via canonical PUT route.
    """
    token = role_test_env["hod_token"]
    payload = {"verification_status": "VERIFIED"}

    # Attempt verify student in ECE -> 403
    res_out = client.put(
        f"/api/students/{role_test_env['student_ece_id']}/verify",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_out.status_code == 403, f"Expected 403 when HOD verifies outside department: {res_out.text}"

    # Verify student inside department (CSE) -> 200
    res_in = client.put(
        f"/api/students/{role_test_env['student_cse_id']}/verify",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_in.status_code == 200, f"Expected 200 when HOD verifies within department: {res_in.text}"
    assert res_in.json()["verification_status"] == "VERIFIED"


def test_05_tnp_can_verify_student_profiles(client: TestClient, role_test_env):
    """
    5. TNP can verify student profiles across any department via canonical PUT route.
    """
    token = role_test_env["tnp_token"]
    payload = {"verification_status": "VERIFIED"}
    res = client.put(
        f"/api/students/{role_test_env['student_ece_id']}/verify",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200, f"TNP should verify any student profile: {res.text}"
    assert res.json()["verification_status"] == "VERIFIED"


def test_06_tnp_can_register_parent_contacts(client: TestClient, role_test_env):
    """
    6. TNP can register parent contacts university-wide; HOD is departmental.
    """
    tnp_token = role_test_env["tnp_token"]
    hod_token = role_test_env["hod_token"]
    student_ece_id = role_test_env["student_ece_id"]

    # 1. HOD cannot register parent for student outside department (ECE)
    res_hod_fail = client.post(
        f"/api/parent/register?student_id={student_ece_id}&parent_name=HODOuterParent&mobile_number=9876543210",
        headers={"Authorization": f"Bearer {hod_token}"}
    )
    assert res_hod_fail.status_code == 403, f"HOD should be forbidden outside department: {res_hod_fail.text}"

    # 2. TNP can register parent for any student (e.g. ECE)
    res_tnp_success = client.post(
        f"/api/parent/register?student_id={student_ece_id}&parent_name=TNPGlobalParent&mobile_number=9876543211",
        headers={"Authorization": f"Bearer {tnp_token}"}
    )
    assert res_tnp_success.status_code == 200, f"TNP should be allowed to register parent: {res_tnp_success.text}"


def test_07_tnp_can_access_university_wide_student_data(client: TestClient, role_test_env):
    """
    7. TNP can access university-wide student data (list and details across departments).
    """
    token = role_test_env["tnp_token"]
    res_list = client.get("/api/students/list", headers={"Authorization": f"Bearer {token}"})
    assert res_list.status_code == 200, f"TNP should access student list: {res_list.text}"

    # CSE student
    res_cse = client.get(f"/api/students/{role_test_env['student_cse_id']}", headers={"Authorization": f"Bearer {token}"})
    assert res_cse.status_code == 200

    # ECE student
    res_ece = client.get(f"/api/students/{role_test_env['student_ece_id']}", headers={"Authorization": f"Bearer {token}"})
    assert res_ece.status_code == 200


def test_08_tnp_can_create_update_and_archive_placement_drives(client: TestClient, role_test_env):
    """
    8. TNP can create, update, and archive placement drives.
    """
    token = role_test_env["tnp_token"]

    # 1. Create drive
    drive_payload = {
        "company_name": "TNP Automated Test Corp",
        "role": "Software Engineer Intern",
        "package_lpa": 14.5,
        "location": "Bengaluru",
        "cgpa_cutoff": 7.0,
        "allowed_depts": "CSE,ECE",
        "allowed_backlogs": 0,
        "interview_date": (date.today() + timedelta(days=20)).isoformat(),
        "deadline": (date.today() + timedelta(days=10)).isoformat(),
        "status": "REGISTRATION_OPEN",
        "batch": "2026"
    }
    create_res = client.post("/api/drives", json=drive_payload, headers={"Authorization": f"Bearer {token}"})
    assert create_res.status_code == 200, f"TNP should be able to create drive: {create_res.text}"
    drive_id = create_res.json()["id"]

    # 2. Update drive
    update_payload = dict(drive_payload)
    update_payload["package_lpa"] = 16.0
    update_res = client.put(f"/api/drives/{drive_id}", json=update_payload, headers={"Authorization": f"Bearer {token}"})
    assert update_res.status_code == 200, f"TNP should be able to update drive: {update_res.text}"
    assert update_res.json()["package_lpa"] == 16.0

    # 3. Archive drive
    archive_res = client.put(f"/api/drives/{drive_id}/archive", headers={"Authorization": f"Bearer {token}"})
    assert archive_res.status_code == 200, f"TNP should be able to archive drive: {archive_res.text}"
    assert archive_res.json()["status"] == "ARCHIVED"


def test_09_tnp_cannot_edit_system_permissions(client: TestClient, role_test_env):
    """
    9. TNP cannot edit system permissions (/api/permissions -> 403).
    """
    token = role_test_env["tnp_token"]
    res_list = client.get("/api/permissions", headers={"Authorization": f"Bearer {token}"})
    assert res_list.status_code == 403, f"TNP must not list permissions: {res_list.text}"

    grant_payload = {
        "user_id": role_test_env["hod_id"],
        "module": "Student Performance",
        "scope": "ALL",
        "scope_value": "ALL",
        "action": "EDIT",
        "duration_days": 7
    }
    res_grant = client.post("/api/permissions/grant", json=grant_payload, headers={"Authorization": f"Bearer {token}"})
    assert res_grant.status_code == 403, f"TNP must not grant permissions: {res_grant.text}"


def test_10_faculty_behavior_remains_unchanged_and_scoped(client: TestClient, role_test_env):
    """
    10. Faculty behavior remains unchanged and scoped to department.
    """
    token = role_test_env["faculty_token"]

    # Profile includes faculty_profile
    res_prof = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {token}"})
    assert res_prof.status_code == 200
    assert res_prof.json()["role"] == "faculty"
    assert res_prof.json()["faculty_profile"]["dept_id"] == role_test_env["dept_cse_id"]

    # In-dept student -> 200
    res_in = client.get(f"/api/students/{role_test_env['student_cse_id']}", headers={"Authorization": f"Bearer {token}"})
    assert res_in.status_code == 200

    # Out-of-dept student -> 403
    res_out = client.get(f"/api/students/{role_test_env['student_ece_id']}", headers={"Authorization": f"Bearer {token}"})
    assert res_out.status_code == 403


def test_11_admin_can_provision_valid_hod_account(client: TestClient, admin_token, role_test_env):
    """
    11. Admin can provision a valid HOD account with linked Faculty record in the database.
    """
    from backend.app.database import SessionLocal
    payload = {
        "name": "Prof. ECE HOD Provisioned",
        "email": "hod.ece.provisioned@platform.edu",
        "password": "securepassword123",
        "dept_id": role_test_env["dept_ece_id"],
        "designation": "Head of ECE Department",
        "role": "hod"
    }
    response = client.post("/api/auth/faculty", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200, f"Admin should provision HOD account: {response.text}"
    data = response.json()
    assert data["role"] == "hod"
    assert data["dept_id"] == role_test_env["dept_ece_id"]
    assert data["designation"] == "Head of ECE Department"
    assert "password" not in data
    assert "password_hash" not in data

    # Direct database verification: Linked Faculty record must exist
    db_check = SessionLocal()
    fac_record = db_check.query(Faculty).filter(Faculty.id == data["id"]).first()
    db_check.close()
    assert fac_record is not None, "Linked Faculty record must exist for HOD"
    assert fac_record.dept_id == role_test_env["dept_ece_id"]


def test_12_admin_can_provision_valid_tnp_account_without_faculty_record(client: TestClient, admin_token):
    """
    12. Admin can provision a valid TNP account without department restrictions and with NO Faculty record.
    """
    from backend.app.database import SessionLocal
    payload = {
        "name": "Central TNP Officer",
        "email": "tnp.central.provisioned@platform.edu",
        "password": "securepassword123",
        "role": "tnp"
    }
    response = client.post("/api/auth/staff", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200, f"Admin should provision TNP account: {response.text}"
    data = response.json()
    assert data["role"] == "tnp"
    assert "password" not in data
    assert "password_hash" not in data

    # Direct database verification: TNP must NOT receive a Faculty record
    db_check = SessionLocal()
    fac_record = db_check.query(Faculty).filter(Faculty.id == data["id"]).first()
    db_check.close()
    assert fac_record is None, "TNP account must NOT produce a Faculty record in the database"


def test_13_non_admin_cannot_provision_staff_accounts(client: TestClient, role_test_env):
    """
    13. Non-admin cannot provision staff accounts (HOD, TNP, Faculty, Student all rejected with 403).
    """
    payload = {
        "name": "Unauthorized Provision Attempt",
        "email": "unauth@platform.edu",
        "password": "password123",
        "role": "faculty",
        "dept_id": role_test_env["dept_cse_id"]
    }
    for token_key in ["hod_token", "faculty_token", "tnp_token"]:
        token = role_test_env[token_key]
        res = client.post("/api/auth/faculty", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403, f"{token_key} should receive 403 when provisioning staff: {res.text}"

    # Unauthenticated -> 401
    res_noauth = client.post("/api/auth/faculty", json=payload)
    assert res_noauth.status_code == 401


def test_14_invalid_role_provisioning_or_duplicate_hod_rejected(client: TestClient, admin_token, role_test_env):
    """
    14. Invalid role provisioning, missing department, duplicate HOD, or invalid email is rejected.
    """
    # 1. Invalid role
    res_bad_role = client.post(
        "/api/auth/faculty",
        json={"name": "Bad Role", "email": "badrole@test.edu", "password": "password123", "role": "superuser"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_bad_role.status_code == 400
    assert "Invalid staff role" in res_bad_role.text

    # 2. HOD without department
    res_no_dept = client.post(
        "/api/auth/faculty",
        json={"name": "No Dept HOD", "email": "nodept@test.edu", "password": "password123", "role": "hod"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_no_dept.status_code == 400
    assert "Department ID is required" in res_no_dept.text

    # 3. Duplicate HOD in same department (CSE already has test_hod_cse)
    res_dup_hod = client.post(
        "/api/auth/faculty",
        json={
            "name": "Second CSE HOD",
            "email": "second.cse.hod@test.edu",
            "password": "password123",
            "role": "hod",
            "dept_id": role_test_env["dept_cse_id"]
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_dup_hod.status_code == 400
    assert "already has an assigned Head of Department" in res_dup_hod.text

    # 4. Short password
    res_short_pwd = client.post(
        "/api/auth/faculty",
        json={
            "name": "Short Pwd",
            "email": "shortpwd@test.edu",
            "password": "123",
            "role": "faculty",
            "dept_id": role_test_env["dept_cse_id"]
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_short_pwd.status_code == 400
    assert "at least 6 characters" in res_short_pwd.text

    # 5. Non-existent department ID
    res_nonexistent_dept = client.post(
        "/api/auth/faculty",
        json={
            "name": "Nonexistent Dept Faculty",
            "email": "nonexistent.dept@test.edu",
            "password": "password123",
            "role": "faculty",
            "dept_id": 99999
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_nonexistent_dept.status_code == 400
    assert "does not exist" in res_nonexistent_dept.text

    # 6. Case-insensitive duplicate email rejection
    res_case_dup = client.post(
        "/api/auth/faculty",
        json={
            "name": "Uppercase Email Duplicate",
            "email": "HOD.ECE.PROVISIONED@PLATFORM.EDU",
            "password": "password123",
            "role": "faculty",
            "dept_id": role_test_env["dept_cse_id"]
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_case_dup.status_code == 400
    assert "already registered" in res_case_dup.text

    # 7. Malformed email address rejection (Pydantic EmailStr validation)
    res_bad_email = client.post(
        "/api/auth/faculty",
        json={
            "name": "Malformed Email Staff",
            "email": "not-an-email-address",
            "password": "password123",
            "role": "faculty",
            "dept_id": role_test_env["dept_cse_id"]
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_bad_email.status_code in [400, 422]


def test_15_frontend_route_allows_tnp_on_admin_drives():
    """
    15. Static route check: App.tsx allows ['admin', 'tnp'] on /admin/drives.
    """
    app_tsx = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    assert "path=\"/admin/drives\"" in app_tsx
    import re
    match = re.search(r'path="/admin/drives"[\s\S]*?<ProtectedRoute allowedRoles=\{([^}]+)\}>', app_tsx)
    assert match is not None, "Could not find ProtectedRoute on /admin/drives in App.tsx"
    roles_str = match.group(1)
    assert "'admin'" in roles_str
    assert "'tnp'" in roles_str


def test_16_failed_provisioning_rolls_back_without_leaving_user(client: TestClient, admin_token, role_test_env):
    """
    16. Failed provisioning (due to non-existent department) leaves zero orphaned User records.
    """
    from backend.app.database import SessionLocal
    failed_email = "rollback.test@platform.edu"

    # Attempt provisioning with invalid dept_id
    res = client.post(
        "/api/auth/faculty",
        json={
            "name": "Rollback Test User",
            "email": failed_email,
            "password": "password123",
            "role": "faculty",
            "dept_id": 88888
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 400

    # Query DB to assert no User record was persisted
    db = SessionLocal()
    user = db.query(User).filter(User.email == failed_email).first()
    db.close()
    assert user is None, "Failed provisioning must roll back and not leave an orphaned User record in the database"


def test_17_tnp_cannot_access_system_logs_report(client: TestClient, role_test_env):
    """
    17. TNP receives HTTP 403 when requesting admin system logs report.
    """
    token = role_test_env["tnp_token"]
    res = client.get("/api/analytics/reports?report_type=logs", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403, f"TNP must be blocked from system logs: {res.text}"


def test_18_canonical_api_routes_work_and_removed_aliases_fail(client: TestClient, role_test_env):
    """
    18. Canonical routes (PUT /verify, POST /register) work; removed aliases return 404 or 405.
    """
    tnp_token = role_test_env["tnp_token"]
    student_id = role_test_env["student_ece_id"]

    # 1. Removed student verify alias returns 404 or 405
    res_bad_student = client.post(
        f"/api/students/{student_id}/verify-profile",
        json={"verification_status": "VERIFIED"},
        headers={"Authorization": f"Bearer {tnp_token}"}
    )
    assert res_bad_student.status_code in [404, 405], f"Removed alias should not exist: {res_bad_student.status_code}"

    # 2. Canonical student verify works (PUT /api/students/{id}/verify)
    res_good_student = client.put(
        f"/api/students/{student_id}/verify",
        json={"verification_status": "VERIFIED"},
        headers={"Authorization": f"Bearer {tnp_token}"}
    )
    assert res_good_student.status_code == 200

    # 3. Removed parent-contact alias returns 404 or 405
    res_bad_parent = client.post(
        f"/api/parent/parent-contact?student_id={student_id}&parent_name=Test&mobile_number=9876543210",
        headers={"Authorization": f"Bearer {tnp_token}"}
    )
    assert res_bad_parent.status_code in [404, 405], f"Removed alias should not exist: {res_bad_parent.status_code}"

    # 4. Canonical parent registration works (POST /api/parent/register)
    res_good_parent = client.post(
        f"/api/parent/register?student_id={student_id}&parent_name=CanonicalParent&mobile_number=9876543212",
        headers={"Authorization": f"Bearer {tnp_token}"}
    )
    assert res_good_parent.status_code == 200


def test_19_frontend_source_does_not_use_removed_aliases():
    """
    19. Frontend source code does not call removed aliases (verify-profile or parent-contact).
    """
    for file_path in Path("frontend/src").rglob("*.ts*"):
        content = file_path.read_text(encoding="utf-8")
        assert "verify-profile" not in content, f"Frontend file {file_path} unexpectedly references verify-profile"
        assert "parent-contact" not in content, f"Frontend file {file_path} unexpectedly references parent-contact"
