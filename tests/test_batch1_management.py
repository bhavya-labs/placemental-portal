import json
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import (
    Base, User, Student, Department, Faculty, Permission, SystemLog, PlacementDrive
)
from backend.app.schemas import StudentUpdate, FacultyUpdateRequest
from backend.app.routers.students import update_student
from backend.app.routers.auth import update_faculty_account
from backend.app.auth import enforce_student_scope, get_permitted_student_query
from datetime import datetime, timedelta

# Isolated in-memory SQLite database fixture for Batch 1 tests
@pytest.fixture(scope="module")
def isolated_db():
    engine = create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed Departments
    d1 = Department(id=1, name="Computer Science & Engineering", code="CSE")
    d2 = Department(id=2, name="Information Technology", code="IT")
    d3 = Department(id=3, name="Electronics & Communication", code="ECE")
    session.add_all([d1, d2, d3])
    session.commit()

    # Seed Users
    admin_u = User(id=1, email="admin@institution.edu", name="System Admin", role="admin", password_hash="hash")
    faculty_u = User(id=2, email="coord.cse@institution.edu", name="Dr. Ramanathan", role="faculty", password_hash="hash")
    other_fac_u = User(id=3, email="coord.it@institution.edu", name="Dr. Sunita", role="faculty", password_hash="hash")
    std1_u = User(id=4, email="student.cse@institution.edu", name="Ananya Sharma", role="student", password_hash="hash")
    std2_u = User(id=5, email="student.it@institution.edu", name="Rohan Verma", role="student", password_hash="hash")
    parent_u = User(id=6, email="parent.cse@institution.edu", name="Sharma Sr.", role="parent", password_hash="hash")
    session.add_all([admin_u, faculty_u, other_fac_u, std1_u, std2_u, parent_u])
    session.commit()

    # Seed Faculty profiles
    f1 = Faculty(id=2, dept_id=1, designation="Assistant Professor")
    f2 = Faculty(id=3, dept_id=2, designation="Associate Professor")
    session.add_all([f1, f2])

    # Seed Department Permissions for Faculty 1 (CSE)
    now = datetime.utcnow()
    p1 = Permission(
        user_id=2,
        module="Student Performance",
        scope="DEPARTMENT",
        scope_value="CSE",
        action="VIEW,EDIT,EXPORT",
        start_date=now - timedelta(days=10),
        expiry_date=now + timedelta(days=100),
        status="Active"
    )
    p2 = Permission(
        user_id=2,
        module="Placement Drives",
        scope="DEPARTMENT",
        scope_value="CSE",
        action="VIEW,EDIT",
        start_date=now - timedelta(days=10),
        expiry_date=now + timedelta(days=100),
        status="Active"
    )
    # Inactive department-scoped permission to test that inactive records are NOT modified
    p_inactive = Permission(
        user_id=2,
        module="Historical Archives",
        scope="DEPARTMENT",
        scope_value="CSE",
        action="VIEW",
        start_date=now - timedelta(days=200),
        expiry_date=now - timedelta(days=10),
        status="Inactive"
    )
    # Non-department-scoped permissions to test preservation
    p_special = Permission(
        user_id=2,
        module="System Reports",
        scope="ALL",
        scope_value=None,
        action="VIEW",
        start_date=now - timedelta(days=10),
        expiry_date=now + timedelta(days=100),
        status="Active"
    )
    p_section = Permission(
        user_id=2,
        module="Section Proctor",
        scope="SECTION",
        scope_value="A",
        action="VIEW,EDIT",
        start_date=now - timedelta(days=10),
        expiry_date=now + timedelta(days=100),
        status="Active"
    )
    session.add_all([p1, p2, p_inactive, p_special, p_section])

    # Seed Students
    s1 = Student(
        id=4,
        dept_id=1,
        gender="Female",
        batch="2026",
        section="A",
        phone="9876543210",
        cgpa=8.5,
        attendance=90.0,
        backlogs=0,
        status="Unplaced",
        skills=json.dumps(["Python", "SQL"])
    )
    s2 = Student(
        id=5,
        dept_id=2,
        gender="Male",
        batch="2026",
        section="B",
        phone="9876543211",
        cgpa=7.8,
        attendance=82.0,
        backlogs=1,
        status="Unplaced",
        skills=json.dumps(["Java", "Spring"])
    )
    session.add_all([s1, s2])
    session.commit()

    yield session, Session
    session.close()


def test_1_admin_edits_student_skills_using_array(isolated_db):
    """1. Admin edits student skills using a JSON/Python list array."""
    db, _ = isolated_db
    admin = db.query(User).filter(User.role == "admin").first()
    student_id = 4

    skills_array = ["Python", "FastAPI", "PostgreSQL", "Docker"]
    update_payload = StudentUpdate(skills=skills_array)

    resp = update_student(student_id=student_id, student_data=update_payload, current_user=admin, db=db)
    assert resp["student_id"] == student_id

    # Verify storage in DB is valid JSON list
    db_student = db.query(Student).filter(Student.id == student_id).first()
    parsed_skills = json.loads(db_student.skills)
    assert isinstance(parsed_skills, list)
    assert parsed_skills == skills_array


def test_2_admin_edits_student_skills_using_comma_separated_string(isolated_db):
    """2. Admin edits student skills using a comma-separated string; normalized into JSON list."""
    db, _ = isolated_db
    admin = db.query(User).filter(User.role == "admin").first()
    student_id = 4

    skills_csv = "Machine Learning, Deep Learning, PyTorch, Scikit-Learn"
    update_payload = StudentUpdate(skills=skills_csv)

    resp = update_student(student_id=student_id, student_data=update_payload, current_user=admin, db=db)
    assert resp["student_id"] == student_id

    # Verify storage in DB was normalized to JSON list
    db_student = db.query(Student).filter(Student.id == student_id).first()
    parsed_skills = json.loads(db_student.skills)
    assert isinstance(parsed_skills, list)
    assert parsed_skills == ["Machine Learning", "Deep Learning", "PyTorch", "Scikit-Learn"]


def test_3_admin_updates_student_name_email_and_department(isolated_db):
    """3. Admin updates student name, email, and department reference with uniqueness check."""
    db, _ = isolated_db
    admin = db.query(User).filter(User.role == "admin").first()
    student_id = 4

    update_payload = StudentUpdate(
        name="Ananya Sharma-Gupta",
        email="ananya.gupta@institution.edu",
        dept_id=2,  # Move to IT
        batch="2026",
        section="C",
        status="Unplaced"
    )

    resp = update_student(student_id=student_id, student_data=update_payload, current_user=admin, db=db)
    assert resp["student_id"] == student_id

    db_student = db.query(Student).filter(Student.id == student_id).first()
    assert db_student.user.name == "Ananya Sharma-Gupta"
    assert db_student.user.email == "ananya.gupta@institution.edu"
    assert db_student.dept_id == 2
    assert db_student.section == "C"

    # Test duplicate email rejection
    duplicate_payload = StudentUpdate(email="rohan.verma@institution.edu")
    # First make sure student 5 has this email
    s2_user = db.query(User).filter(User.id == 5).first()
    s2_user.email = "rohan.verma@institution.edu"
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        update_student(student_id=4, student_data=duplicate_payload, current_user=admin, db=db)
    assert exc_info.value.status_code == 400
    assert "already in use" in exc_info.value.detail


def test_4_student_cannot_modify_locked_academic_fields(isolated_db):
    """4. Student attempts to modify locked academic fields (CGPA, attendance, backlogs) and receives 403."""
    db, _ = isolated_db
    student_user = db.query(User).filter(User.id == 4).first()

    # Attempt to elevate CGPA from 8.5 to 9.8
    with pytest.raises(HTTPException) as exc_info:
        update_student(
            student_id=4,
            student_data=StudentUpdate(cgpa=9.8),
            current_user=student_user,
            db=db
        )
    assert exc_info.value.status_code == 403
    assert "Academic metric 'cgpa' cannot be modified directly" in exc_info.value.detail

    # Attempt to change department as student
    with pytest.raises(HTTPException) as exc_info:
        update_student(
            student_id=4,
            student_data=StudentUpdate(dept_id=1),
            current_user=student_user,
            db=db
        )
    assert exc_info.value.status_code == 403
    assert "Academic metric 'dept_id' cannot be modified directly" in exc_info.value.detail

    # Allowed student self-edit (e.g. phone and non-academic skills)
    self_edit_payload = StudentUpdate(phone="9123456789", skills=["Python", "Django"])
    resp = update_student(student_id=4, student_data=self_edit_payload, current_user=student_user, db=db)
    assert resp["student_id"] == 4
    db_student = db.query(Student).filter(Student.id == 4).first()
    assert db_student.phone == "9123456789"


def test_5_admin_reassigns_faculty_coordinator_department(isolated_db):
    """5. Admin changes a faculty coordinator from one department to another in a transaction."""
    db, _ = isolated_db
    admin = db.query(User).filter(User.role == "admin").first()
    faculty_id = 2

    # Change Dr. Ramanathan from Dept 1 (CSE) to Dept 2 (IT)
    req = FacultyUpdateRequest(
        name="Dr. K. Ramanathan",
        dept_id=2,
        designation="Professor & Coordinator"
    )

    resp = update_faculty_account(faculty_id=faculty_id, payload=req, current_user=admin, db=db)
    assert resp["dept_id"] == 2
    assert resp["dept_code"] == "IT"
    assert resp["permissions_updated"] == 2

    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    assert faculty.dept_id == 2
    assert faculty.user.name == "Dr. K. Ramanathan"
    assert faculty.designation == "Professor & Coordinator"


def test_6_faculty_permissions_match_destination_department(isolated_db):
    """6. Active department-scoped permissions are updated to destination department;
    inactive department permissions, ALL-scope, and SECTION-scope permissions remain unchanged."""
    db, _ = isolated_db
    faculty_id = 2

    # 1. Active department permissions MUST be updated to destination department "IT"
    active_dept_perms = db.query(Permission).filter(
        Permission.user_id == faculty_id,
        Permission.scope == "DEPARTMENT",
        Permission.status == "Active"
    ).all()

    assert len(active_dept_perms) == 2
    for p in active_dept_perms:
        assert p.scope_value == "IT", f"Expected scope_value 'IT' for active module {p.module}, got {p.scope_value}"

    # 2. Inactive department permissions MUST remain unchanged ("CSE")
    inactive_dept_perms = db.query(Permission).filter(
        Permission.user_id == faculty_id,
        Permission.scope == "DEPARTMENT",
        Permission.status == "Inactive"
    ).all()

    assert len(inactive_dept_perms) == 1
    assert inactive_dept_perms[0].scope_value == "CSE", (
        f"Inactive permission should remain 'CSE', but got '{inactive_dept_perms[0].scope_value}'"
    )

    # 3. ALL-scope permission MUST remain unchanged (scope_value is None)
    all_perm = db.query(Permission).filter(
        Permission.user_id == faculty_id,
        Permission.scope == "ALL"
    ).first()
    assert all_perm is not None
    assert all_perm.scope == "ALL"
    assert all_perm.scope_value is None

    # 4. SECTION-scope permission MUST remain unchanged (scope_value is "A")
    section_perm = db.query(Permission).filter(
        Permission.user_id == faculty_id,
        Permission.scope == "SECTION"
    ).first()
    assert section_perm is not None
    assert section_perm.scope == "SECTION"
    assert section_perm.scope_value == "A"


def test_7_reassigned_faculty_accesses_only_new_department(isolated_db):
    """7. Reassigned faculty coordinator can access only students in their newly assigned department."""
    db, _ = isolated_db
    faculty_user = db.query(User).filter(User.id == 2).first()

    # Query permitted students
    permitted_query = get_permitted_student_query(faculty_user, db, action="VIEW")
    permitted_students = permitted_query.all()

    # Faculty 2 was reassigned to IT (Dept 2)
    # Students in IT should be visible; students in CSE must NOT be returned
    it_student_ids = [s.id for s in db.query(Student).filter(Student.dept_id == 2).all()]
    cse_student_ids = [s.id for s in db.query(Student).filter(Student.dept_id == 1).all()]

    returned_ids = [s.id for s in permitted_students]
    for sid in it_student_ids:
        assert sid in returned_ids, f"IT Student {sid} should be visible"
    for sid in cse_student_ids:
        assert sid not in returned_ids, f"CSE Student {sid} must NOT be visible to reassigned IT faculty"

    # Single student scope enforcement check
    # IT student access succeeds
    it_student = db.query(Student).filter(Student.dept_id == 2).first()
    assert enforce_student_scope(faculty_user, it_student.id, db, "VIEW").id == it_student.id

    # If there is any CSE student, accessing them must raise 403
    cse_student = db.query(Student).filter(Student.dept_id == 1).first()
    if cse_student:
        with pytest.raises(HTTPException) as exc_info:
            enforce_student_scope(faculty_user, cse_student.id, db, "VIEW")
        assert exc_info.value.status_code == 403


def test_8_invalid_department_ids_produce_clean_error(isolated_db):
    """8. Invalid department IDs produce clean 400 validation errors."""
    db, _ = isolated_db
    admin = db.query(User).filter(User.role == "admin").first()

    # Invalid department on faculty update
    with pytest.raises(HTTPException) as exc_info:
        update_faculty_account(
            faculty_id=2,
            payload=FacultyUpdateRequest(name="Dr. Ramanathan", dept_id=99999, designation="Prof"),
            current_user=admin,
            db=db
        )
    assert exc_info.value.status_code == 400
    assert "Invalid department ID: 99999 does not exist" in exc_info.value.detail

    # Invalid department on student update
    with pytest.raises(HTTPException) as exc_info:
        update_student(
            student_id=4,
            student_data=StudentUpdate(dept_id=99999),
            current_user=admin,
            db=db
        )
    assert exc_info.value.status_code == 400
    assert "Invalid department ID: 99999 does not exist" in exc_info.value.detail


def test_9_non_admin_cannot_invoke_administrative_operations(isolated_db):
    """9. Non-admin users cannot invoke administrator-only endpoints."""
    db, _ = isolated_db
    student_user = db.query(User).filter(User.id == 4).first()
    faculty_user = db.query(User).filter(User.id == 2).first()
    parent_user = db.query(User).filter(User.id == 6).first()

    # Student cannot update faculty
    with pytest.raises(HTTPException) as exc_info:
        update_faculty_account(
            faculty_id=2,
            payload=FacultyUpdateRequest(name="Hacker", dept_id=1, designation="Dean"),
            current_user=student_user,
            db=db
        )
    assert exc_info.value.status_code == 403

    # Faculty cannot update other faculty
    with pytest.raises(HTTPException) as exc_info:
        update_faculty_account(
            faculty_id=3,
            payload=FacultyUpdateRequest(name="Faculty", dept_id=1, designation="Prof"),
            current_user=faculty_user,
            db=db
        )
    assert exc_info.value.status_code == 403

    # Parent cannot update student profiles
    with pytest.raises(HTTPException) as exc_info:
        update_student(
            student_id=4,
            student_data=StudentUpdate(skills=["C++"]),
            current_user=parent_user,
            db=db
        )
    assert exc_info.value.status_code == 403


def test_10_refresh_confirms_all_changes_persisted(isolated_db):
    """10. Independent session reload confirms persistence across transactions."""
    _, SessionFactory = isolated_db

    # Create a fresh independent session (simulating page reload)
    new_session = SessionFactory()
    try:
        # Check student updates
        student = new_session.query(Student).filter(Student.id == 4).first()
        assert student.user.name == "Ananya Sharma-Gupta"
        assert student.user.email == "ananya.gupta@institution.edu"
        assert student.dept_id == 2
        assert student.phone == "9123456789"
        parsed_skills = json.loads(student.skills)
        assert "Django" in parsed_skills or "PyTorch" in parsed_skills or "Python" in parsed_skills

        # Check faculty updates
        faculty = new_session.query(Faculty).filter(Faculty.id == 2).first()
        assert faculty.dept_id == 2
        assert faculty.designation == "Professor & Coordinator"
        assert faculty.user.name == "Dr. K. Ramanathan"

        # Check permission sync: active department permissions updated to IT; inactive CSE remains CSE
        active_perms = new_session.query(Permission).filter(
            Permission.user_id == 2,
            Permission.scope == "DEPARTMENT",
            Permission.status == "Active"
        ).all()
        assert len(active_perms) == 2
        for p in active_perms:
            assert p.scope_value == "IT"

        inactive_perms = new_session.query(Permission).filter(
            Permission.user_id == 2,
            Permission.scope == "DEPARTMENT",
            Permission.status == "Inactive"
        ).all()
        assert len(inactive_perms) == 1
        assert inactive_perms[0].scope_value == "CSE"

        section_p = new_session.query(Permission).filter(
            Permission.user_id == 2,
            Permission.scope == "SECTION"
        ).first()
        assert section_p.scope_value == "A"
    finally:
        new_session.close()

