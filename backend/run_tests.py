import os
import sys
os.environ["SMS_ENV"] = "prod"
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, date

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Student, Parent, ParentOTP, Department, PlacementDrive, Application, Interview, Feedback, Permission, Company
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


def get_token(sub: str, role: str, name: str = "") -> str:
    return create_access_token(data={"sub": sub, "role": role, "name": name})

def run_tests():
    print("Initializing test database...")
    setup_db()
    print("Database ready. Starting test assertions...")

    # Test 1: Parent Child Scope Security
    print("- Testing Parent Child Scope Security...")
    token_parent_a = get_token("101", "parent", "Parent A")
    headers = {"Authorization": f"Bearer {token_parent_a}"}
    res = client.get("/api/students/101", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    res = client.get("/api/students/102", headers=headers)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"

    # Test 2: Attendance Parent Scoping
    print("- Testing Attendance Parent Scoping...")
    res = client.get("/api/attendance/academic/101", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    res = client.get("/api/attendance/academic/102", headers=headers)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"

    # Test 3: Faculty Scoping
    print("- Testing Faculty Scoping...")
    token_fac = get_token("faculty.cse@platform.edu", "faculty")
    headers_fac = {"Authorization": f"Bearer {token_fac}"}
    res = client.get("/api/students/101", headers=headers_fac)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    res = client.get("/api/students/102", headers=headers_fac)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"

    # Test 4: TNP Access
    print("- Testing TNP Access...")
    token_tnp = get_token("tnp@platform.edu", "tnp")
    headers_tnp = {"Authorization": f"Bearer {token_tnp}"}
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
    }, headers=headers_tnp)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"

    res = client.put("/api/applications/50/status", json={
        "status": "Selected",
        "current_round": "HR",
        "joining_status": "Accepted",
        "remarks": "Great work"
    }, headers=headers_tnp)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"

    # Test 5: OTP Secure Response
    print("- Testing OTP Secure Response...")
    res = client.post("/api/parent/request-otp", json={
        "roll_number": 101,
        "mobile_number": "9876543210"
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert "otp" not in data, "Leaked otp in response"
    assert "otp_debug" not in data, "Leaked otp_debug in response"

    # Test 6: OTP Rate Limiting
    print("- Testing OTP Rate Limiting...")
    res = client.post("/api/parent/request-otp", json={
        "roll_number": 101,
        "mobile_number": "9876543210"
    })
    assert res.status_code == 400, f"Expected 400 cooldown blockage, got {res.status_code}"

    # Test 7: Smart Eligibility Criteria Verification
    print("- Testing Smart Eligibility Criteria Verification...")
    db = TestingSessionLocal()
    db.query(Application).filter(Application.id == 50).delete()
    db.commit()
    db.close()

    token_student_a = get_token("studenta@platform.edu", "student")
    headers_stud_a = {"Authorization": f"Bearer {token_student_a}"}
    res = client.post("/api/applications", json={"drive_id": 10}, headers=headers_stud_a)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}. Detail: {res.json()}"

    # Student B has CGPA 7.5, which is lower than cutoff 8.0
    token_student_b = get_token("studentb@platform.edu", "student")
    headers_stud_b = {"Authorization": f"Bearer {token_student_b}"}
    res = client.post("/api/applications", json={"drive_id": 10}, headers=headers_stud_b)
    assert res.status_code == 400, f"Expected 400 eligibility block, got {res.status_code}"

    # Test 8: Drive Lifecycle State Transitions
    print("- Testing Drive Lifecycle Transitions...")
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
    }, headers=headers_tnp)
    assert res.status_code == 200, f"Expected 200 transition, got {res.status_code}"

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
        "status": "COMPLETED", # Invalid jump bypassing REG_CLOSED, ASSESSMENT, etc.
        "batch": "2026",
        "min_attendance": 75.0
    }, headers=headers_tnp)
    assert res.status_code == 400, f"Expected 400 invalid transition, got {res.status_code}"

    # Test 9: Bulk Upload Validation Preview
    print("- Testing Bulk Upload Validation Preview...")
    payload_bulk = [
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
    res = client.post("/api/students/bulk-upload?preview=true", json=payload_bulk, headers=headers_fac)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    preview_data = res.json()
    assert preview_data["preview"] is True
    assert preview_data["total"] == 3
    assert preview_data["valid"] == 1
    assert preview_data["duplicates"] == 1
    assert preview_data["invalid"] == 1

    # Test 10: First Profile Submission -> Verified -> Locked
    print("- Testing Profile Submission & Locking Workflow...")
    db = TestingSessionLocal()
    stud_b_db = db.query(Student).filter(Student.id == 102).first()
    assert stud_b_db.verification_status == "UNVERIFIED"
    db.close()

    # First successful update (submission)
    res = client.put("/api/students/102", json={
        "phone": "9999999992",
        "cgpa": 7.5,
        "attendance": 70.0,
        "backlogs": 1,
        "skills": "[\"Python\", \"SQL\"]",
        "github_url": ""
    }, headers=headers_stud_b)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}. Detail: {res.text}"

    # Get student B details and assert verification_status == VERIFIED
    res_get = client.get("/api/students/102", headers=headers_stud_b)
    assert res_get.status_code == 200
    assert res_get.json()["verification_status"] == "VERIFIED"

    # Attempt to change locked institutional field (cgpa)
    res_lock = client.put("/api/students/102", json={
        "phone": "9999999992",
        "cgpa": 8.0,
        "attendance": 70.0,
        "backlogs": 1,
        "skills": "[\"Python\", \"SQL\"]",
        "github_url": ""
    }, headers=headers_stud_b)
    assert res_lock.status_code == 403, f"Expected 403, got {res_lock.status_code}"

    # Verify student-controlled field (github_url) CAN still be updated if institutional fields are unchanged
    res_editable = client.put("/api/students/102", json={
        "phone": "9999999992",
        "cgpa": 7.5,
        "attendance": 70.0,
        "backlogs": 1,
        "skills": "[\"Python\", \"SQL\"]",
        "github_url": "https://github.com/studentb"
    }, headers=headers_stud_b)
    assert res_editable.status_code == 200, f"Expected 200, got {res_editable.status_code}"

    # Get details and confirm student-controlled field updated
    res_get_final = client.get("/api/students/102", headers=headers_stud_b)
    assert res_get_final.json()["github_url"] == "https://github.com/studentb"

    # Test 11: Global Search Scoping & RBAC
    print("- Testing Global Search Scoping & RBAC...")
    # Admin/TNP Search: Case-insensitive, Partial search
    res_search = client.get("/api/search?q=student", headers=headers_tnp)
    assert res_search.status_code == 200, f"Expected 200, got {res_search.status_code}"
    data_search = res_search.json()
    assert len(data_search["students"]) > 0

    res_search_caps = client.get("/api/search?q=STUDENT", headers=headers_tnp)
    assert res_search_caps.status_code == 200
    assert len(res_search_caps.json()["students"]) == len(data_search["students"])

    # No Results
    res_no_results = client.get("/api/search?q=xyz123abc", headers=headers_tnp)
    assert res_no_results.status_code == 200
    assert len(res_no_results.json()["students"]) == 0
    assert len(res_no_results.json()["drives"]) == 0

    # Student Role Bypass Attempt (Expected: 403)
    res_stud_bypass = client.get("/api/search?q=student", headers=headers_stud_b)
    assert res_stud_bypass.status_code == 403, f"Expected 403, got {res_stud_bypass.status_code}"

    # Parent Role scoping (Child A = 101, Child B = 102)
    # parent_a has token_parent_a pointing to student 101
    res_parent_search = client.get("/api/search?q=student", headers=headers)
    assert res_parent_search.status_code == 200
    parent_results = res_parent_search.json()["students"]
    student_ids = [s["id"] for s in parent_results]
    assert 101 in student_ids
    assert 102 not in student_ids

    # Department Scoping (Faculty CSE -> CSE Student 101 is returned, ECE Student 102 is excluded)
    res_fac_search = client.get("/api/search?q=student", headers=headers_fac)
    assert res_fac_search.status_code == 200
    fac_results = res_fac_search.json()["students"]
    fac_student_ids = [s["id"] for s in fac_results]
    assert 101 in fac_student_ids
    assert 102 not in fac_student_ids

    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\nTEST ASSERTION FAILURE: {e}")
        sys.exit(1)
