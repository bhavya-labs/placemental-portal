import os
import pytest
os.environ["SMS_ENV"] = "prod"
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Student, Parent, ParentOTP, Department, PlacementDrive, Application, Interview, Feedback, Permission
from backend.app.auth import get_password_hash, create_access_token

# Setup test SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_portal.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create Departments
    cse = Department(id=1, name="Computer Science", code="CSE")
    ece = Department(id=2, name="Electronics", code="ECE")
    db.add_all([cse, ece])
    db.commit()

    # Create User Passwords
    pwd_hash = get_password_hash("password123")

    # Create Students
    # Student A (CSE)
    user_a = User(id=101, email="studenta@platform.edu", password_hash=pwd_hash, name="Student A", role="student")
    student_a = Student(id=101, dept_id=1, gender="Male", batch="2026", phone="9999999991", cgpa=8.5, attendance=80.0, backlogs=0, status="Unplaced")
    
    # Student B (ECE)
    user_b = User(id=102, email="studentb@platform.edu", password_hash=pwd_hash, name="Student B", role="student")
    student_b = Student(id=102, dept_id=2, gender="Female", batch="2026", phone="9999999992", cgpa=7.5, attendance=70.0, backlogs=1, status="Unplaced")
    
    db.add_all([user_a, student_a, user_b, student_b])
    db.commit()

    # Create Parents
    # Parent A linked to Child A (101)
    parent_a = Parent(id=201, student_id=101, parent_name="Parent A", mobile_number="9876543210", relationship="Father")
    db.add(parent_a)
    db.commit()

    # Create Faculty
    user_faculty_cse = User(id=301, email="faculty.cse@platform.edu", password_hash=pwd_hash, name="CSE Faculty", role="faculty")
    db.add(user_faculty_cse)
    db.commit()

    # Setup permissions for faculty
    now = datetime.utcnow()
    perm_cse = Permission(
        id=1,
        user_id=301,
        module="Student Performance",
        action="VIEW, EDIT",
        scope="DEPARTMENT",
        scope_value="CSE",
        status="Active",
        start_date=now - timedelta(days=1),
        expiry_date=now + timedelta(days=10)
    )
    db.add(perm_cse)

    # Create TNP Coordinator
    user_tnp = User(id=401, email="tnp@platform.edu", password_hash=pwd_hash, name="TNP Officer", role="tnp")
    db.add(user_tnp)
    db.commit()

    # Create Company & Drives
    google = Company(id=1, name="Google", industry="Software", website="google.com", description="Tech")
    db.add(google)
    db.commit()

    drive_active = PlacementDrive(
        id=10,
        company_id=1,
        role="SWE",
        package_lpa=25.0,
        location="Bangalore",
        cgpa_cutoff=8.0,
        allowed_depts="CSE,ECE",
        allowed_backlogs=0,
        interview_date=datetime.now().date() + timedelta(days=5),
        deadline=datetime.now().date() + timedelta(days=3),
        status="PUBLISHED",
        batch="2026",
        min_attendance=75.0
    )
    db.add(drive_active)
    db.commit()

    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def get_token(sub: str, role: str, name: str = "") -> str:
    return create_access_token(data={"sub": sub, "role": role, "name": name})


# ==========================================
# TEST SUITE CASES
# ==========================================

def test_parent_child_scope_security():
    # Parent A (access token maps sub to student_id 101)
    token_parent_a = get_token("101", "parent", "Parent A")
    headers = {"Authorization": f"Bearer {token_parent_a}"}

    # Access own child Student A -> 200
    res = client.get("/api/students/101", headers=headers)
    assert res.status_code == 200

    # Access other child Student B -> 403
    res = client.get("/api/students/102", headers=headers)
    assert res.status_code == 403


def test_attendance_parent_scoping():
    token_parent_a = get_token("101", "parent", "Parent A")
    headers = {"Authorization": f"Bearer {token_parent_a}"}

    # Access child A attendance -> 200
    res = client.get("/api/attendance/academic/101", headers=headers)
    assert res.status_code == 200

    # Access child B attendance -> 403
    res = client.get("/api/attendance/academic/102", headers=headers)
    assert res.status_code == 403


def test_faculty_scoping():
    token_fac = get_token("faculty.cse@platform.edu", "faculty")
    headers = {"Authorization": f"Bearer {token_fac}"}

    # CSE Faculty accesses CSE Student A -> 200
    res = client.get("/api/students/101", headers=headers)
    assert res.status_code == 200

    # CSE Faculty accesses ECE Student B -> 403
    res = client.get("/api/students/102", headers=headers)
    assert res.status_code == 403


def test_tnp_access():
    token_tnp = get_token("tnp@platform.edu", "tnp")
    headers = {"Authorization": f"Bearer {token_tnp}"}

    # Schedule interview -> 200 (Mock request details)
    # First create a mock application
    db = TestingSessionLocal()
    app_rec = Application(id=50, student_id=101, drive_id=10, status="Applied", current_round="Applied")
    db.add(app_rec)
    db.commit()
    db.close()

    res = client.post("/api/interviews", json={
        "application_id": 50,
        "round_name": "Technical",
        "interview_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "remarks": "Google interview"
    }, headers=headers)
    assert res.status_code == 200

    # Update status -> 200
    res = client.put("/api/applications/50/status", json={
        "status": "Selected",
        "current_round": "HR",
        "joining_status": "Accepted",
        "remarks": "Great work"
    }, headers=headers)
    assert res.status_code == 200


def test_otp_secure_api():
    # Request OTP -> 200
    res = client.post("/api/parent/request-otp", json={
        "roll_number": 101,
        "mobile_number": "9876543210"
    })
    assert res.status_code == 200
    data = res.json()
    
    # Assert OTP is hidden and never leaked
    assert "otp" not in data
    assert "otp_debug" not in data
    assert "hashed_otp" not in data


def test_otp_rate_limiting():
    # Trigger 2nd request immediately -> Cooldown triggered
    res = client.post("/api/parent/request-otp", json={
        "roll_number": 101,
        "mobile_number": "9876543210"
    })
    # Since resend cooldown is 60 seconds, it should return 400
    assert res.status_code == 400
    assert "Please wait" in res.json()["detail"]


def test_smart_eligibility():
    token_student_a = get_token("studenta@platform.edu", "student")
    headers = {"Authorization": f"Bearer {token_student_a}"}

    # Student A has CGPA 8.5, attendance 80, backlogs 0 -> Eligible -> 200
    res = client.post("/api/applications", json={"drive_id": 10}, headers=headers)
    assert res.status_code == 200


def test_smart_eligibility_failure():
    # Student B has CGPA 7.5 (cutoff 8.0) and backlogs 1 (cutoff 0) and attendance 70 (cutoff 75)
    # Register Student B token and apply -> 400
    token_student_b = get_token("studentb@platform.edu", "student")
    headers = {"Authorization": f"Bearer {token_student_b}"}

    res = client.post("/api/applications", json={"drive_id": 10}, headers=headers)
    assert res.status_code == 400
    # Returns specific academic reason
    assert "CGPA" in res.json()["detail"] or "attendance" in res.json()["detail"] or "backlogs" in res.json()["detail"]


def test_drive_transitions():
    token_tnp = get_token("tnp@platform.edu", "tnp")
    headers = {"Authorization": f"Bearer {token_tnp}"}

    # Update drive: transition PUBLISHED -> REGISTRATION_OPEN -> 200
    res = client.put("/api/drives/10", json={
        "company_id": 1,
        "role": "SWE",
        "package_lpa": 25.0,
        "location": "Bangalore",
        "cgpa_cutoff": 8.0,
        "allowed_depts": "CSE,ECE",
        "allowed_backlogs": 0,
        "interview_date": (datetime.now() + timedelta(days=5)).date().isoformat(),
        "deadline": (datetime.now() + timedelta(days=3)).date().isoformat(),
        "status": "REGISTRATION_OPEN",
        "batch": "2026",
        "min_attendance": 75.0
    }, headers=headers)
    assert res.status_code == 200

    # Invalid transition: REGISTRATION_OPEN -> COMPLETED (bypassing REGISTRATION_CLOSED, ASSESSMENT, etc.) -> 400
    res = client.put("/api/drives/10", json={
        "company_id": 1,
        "role": "SWE",
        "package_lpa": 25.0,
        "location": "Bangalore",
        "cgpa_cutoff": 8.0,
        "allowed_depts": "CSE,ECE",
        "allowed_backlogs": 0,
        "interview_date": (datetime.now() + timedelta(days=5)).date().isoformat(),
        "deadline": (datetime.now() + timedelta(days=3)).date().isoformat(),
        "status": "COMPLETED",
        "batch": "2026",
        "min_attendance": 75.0
    }, headers=headers)
    assert res.status_code == 400
    assert "Invalid lifecycle status transition" in res.json()["detail"]


def test_bulk_upload_preview():
    token_fac = get_token("faculty.cse@platform.edu", "faculty")
    headers = {"Authorization": f"Bearer {token_fac}"}

    payload = [
        {
            "email": "newstudent@platform.edu",
            "name": "New Student",
            "department": "CSE",
            "cgpa": 8.0,
            "attendance": 90.0,
            "backlogs": 0
        },
        {
            "email": "studenta@platform.edu",  # Duplicate email
            "name": "Student A",
            "department": "CSE",
            "cgpa": 8.5,
            "attendance": 80.0,
            "backlogs": 0
        },
        {
            "email": "badstudent@platform.edu",
            "name": "Bad Student",
            "department": "CSE",
            "cgpa": -1.0,  # Invalid CGPA
            "attendance": 85.0,
            "backlogs": 0
        }
    ]

    # Test preview mode (preview=True)
    res = client.post("/api/students/bulk-upload?preview=true", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["preview"] is True
    assert data["total"] == 3
    assert data["valid"] == 1
    assert data["duplicates"] == 1
    assert data["invalid"] == 1
