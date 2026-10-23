import sys
import os
from pathlib import Path
from datetime import date, timedelta

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal, Base, engine
from backend.app.models import (
    User, Student, Department, Company, PlacementDrive, Application, 
    Faculty, Parent, Notification, Interview, Feedback
)
from backend.app.auth import create_access_token, get_password_hash
from datetime import datetime
import json

def seed_minimal_test_fixtures(db):
    """
    Ensure the test database has the minimum required test fixtures to run the
    test suite in an isolated, self-contained manner (e.g. fresh CI database).
    Only populates missing records; never drops tables or wipes existing data.
    """
    # Safety guard: refuse to seed against live production Render/external database
    db_url = str(engine.url).lower()
    if "render.com" in db_url or "onrender.com" in db_url or "dpg-" in db_url:
        raise RuntimeError("Refusing to run test fixture seeding against production Render database!")

    # 0. Early exit if the database is already fully provisioned (e.g. existing local database)
    admin_u = db.query(User).filter(User.role == "admin").first()
    faculty_u = db.query(User).filter(User.role == "faculty").first()
    students_count = db.query(Student).count()
    drive4 = db.query(PlacementDrive).filter(PlacementDrive.id == 4).first()
    drive6 = db.query(PlacementDrive).filter(PlacementDrive.id == 6).first()
    feedbacks_count = db.query(Feedback).count()

    if admin_u and faculty_u and students_count >= 20 and drive4 and drive6 and feedbacks_count >= 8:
        return

    # 1. Departments
    depts = {}
    for code, name in [
        ("CSE", "Computer Science & Engineering"),
        ("IT", "Information Technology"),
        ("ECE", "Electronics & Communication Engineering"),
        ("EEE", "Electrical & Electronics Engineering"),
        ("MECH", "Mechanical Engineering"),
        ("CIVIL", "Civil Engineering"),
    ]:
        d = db.query(Department).filter(Department.code == code).first()
        if not d:
            d = Department(name=name, code=code)
            db.add(d)
            db.flush()
        depts[code] = d

    # 2. Shared test password hash
    shared_hash = get_password_hash("password123")

    # 3. Admin Users
    for email in ["admin@college.edu", "admin@platform.edu"]:
        if not db.query(User).filter(User.email == email).first():
            db.add(User(
                email=email,
                name="System Administrator",
                role="admin",
                password_hash=shared_hash
            ))
    db.flush()

    # 4. Faculty User
    fac_user = db.query(User).filter(User.email == "faculty.cse@platform.edu").first()
    if not fac_user:
        fac_user = User(
            email="faculty.cse@platform.edu",
            name="Dr. CSE Faculty",
            role="faculty",
            password_hash=shared_hash
        )
        db.add(fac_user)
        db.flush()

    if not db.query(Faculty).filter(Faculty.id == fac_user.id).first():
        db.add(Faculty(
            id=fac_user.id,
            dept_id=depts["CSE"].id,
            designation="HOD"
        ))
    db.flush()

    # 5. Companies
    comp_map = {}
    for cname in ["TechCorp Solutions", "Apple", "Infosys"]:
        c = db.query(Company).filter(Company.name == cname).first()
        if not c:
            c = Company(
                name=cname,
                industry="Technology",
                website=f"https://{cname.lower().replace(' ', '')}.example.com",
                description=f"{cname} profile"
            )
            db.add(c)
            db.flush()
        comp_map[cname] = c

    # 6. Placement Drives (Drive 4 for Apple, Drive 6 for Infosys)
    for did, comp_name, role in [(4, "Apple", "Software Engineer"), (6, "Infosys", "Systems Engineer")]:
        if not db.query(PlacementDrive).filter(PlacementDrive.id == did).first():
            db.add(PlacementDrive(
                id=did,
                company_id=comp_map[comp_name].id,
                role=role,
                package_lpa=12.0,
                location="Bengaluru",
                cgpa_cutoff=6.0,
                allowed_depts="ALL",
                allowed_backlogs=2,
                batch="2026",
                deadline=date.today() - timedelta(days=5),
                interview_date=date.today() - timedelta(days=2),
                status="Completed"
            ))
    db.flush()

    # 7. Students (at least 20 students for ML 80/20 stratified split & at-risk tests)
    existing_students = db.query(Student).count()
    if existing_students < 20:
        for i in range(1, 21):
            s_email = f"student{i}@institution.edu"
            u = db.query(User).filter(User.email == s_email).first()
            if not u:
                u = User(
                    email=s_email,
                    name=f"Student {i}",
                    role="student",
                    password_hash=shared_hash
                )
                db.add(u)
                db.flush()

            s = db.query(Student).filter(Student.id == u.id).first()
            if not s:
                if i <= 5:
                    status = "At Risk"
                    cgpa = 5.5
                    attendance = 62.0
                    backlogs = 3
                    coding = 45.0
                elif i <= 13:
                    status = "Placed"
                    cgpa = 8.8
                    attendance = 92.0
                    backlogs = 0
                    coding = 88.0
                else:
                    status = "Unplaced"
                    cgpa = 7.5
                    attendance = 80.0
                    backlogs = 0
                    coding = 70.0

                s = Student(
                    id=u.id,
                    dept_id=depts["CSE"].id,
                    gender="Male" if i % 2 == 0 else "Female",
                    batch="2026",
                    phone=f"98765432{i:02d}",
                    cgpa=cgpa,
                    attendance=attendance,
                    backlogs=backlogs,
                    skills=json.dumps(["Python", "SQL", "Git", "React", "DSA"]),
                    projects=json.dumps([{"title": "Web Portal", "tech": "React"}]),
                    certifications=json.dumps(["AWS Cloud Practitioner"]),
                    leetcode_score=int(coding * 2),
                    codechef_score=int(coding * 1.5),
                    hackerrank_score=int(coding),
                    status=status,
                    verification_status="VERIFIED",
                    section="A"
                )
                db.add(s)
                db.flush()

    # 8. Ensure parent record exists for OTP tests
    if not db.query(Parent).first():
        st = db.query(Student).first()
        if st:
            db.add(Parent(
                student_id=st.id,
                parent_name="Parent of Student 1",
                mobile_number="9876543210",
                relationship="Father"
            ))
            db.flush()

    # 9. Feedbacks for Drive 4 (>= 5 required) and Drive 6 (>= 3 required)
    d4_feedbacks = (
        db.query(Feedback)
        .join(Interview)
        .join(Application)
        .filter(Application.drive_id == 4)
        .count()
    )
    if d4_feedbacks < 5:
        avail_students = db.query(Student).all()
        for st in avail_students:
            if d4_feedbacks >= 5:
                break
            app = db.query(Application).filter(Application.student_id == st.id, Application.drive_id == 4).first()
            if not app:
                app = Application(student_id=st.id, drive_id=4, status="Interview Scheduled")
                db.add(app)
                db.flush()
            intr = db.query(Interview).filter(Interview.application_id == app.id).first()
            if not intr:
                intr = Interview(
                    application_id=app.id,
                    student_id=st.id,
                    round_name="Technical",
                    status="Passed",
                    interview_date=datetime.utcnow() - timedelta(days=2)
                )
                db.add(intr)
                db.flush()
            fb = db.query(Feedback).filter(Feedback.interview_id == intr.id).first()
            if not fb:
                db.add(Feedback(
                    interview_id=intr.id,
                    difficulty_rating=3,
                    rating=4,
                    questions_asked="DSA, Trees, Reversing a Linked List",
                    experience_text="Comprehensive technical interview with focus on algorithm efficiency.",
                    topic_analysis="DSA",
                    theme="Technical Preparation"
                ))
                db.flush()
                d4_feedbacks += 1

    d6_feedbacks = (
        db.query(Feedback)
        .join(Interview)
        .join(Application)
        .filter(Application.drive_id == 6)
        .count()
    )
    if d6_feedbacks < 3:
        avail_students = db.query(Student).all()
        for st in avail_students:
            if d6_feedbacks >= 3:
                break
            app = db.query(Application).filter(Application.student_id == st.id, Application.drive_id == 6).first()
            if not app:
                app = Application(student_id=st.id, drive_id=6, status="Interview Scheduled")
                db.add(app)
                db.flush()
            intr = db.query(Interview).filter(Interview.application_id == app.id).first()
            if not intr:
                intr = Interview(
                    application_id=app.id,
                    student_id=st.id,
                    round_name="Technical",
                    status="Passed",
                    interview_date=datetime.utcnow() - timedelta(days=2)
                )
                db.add(intr)
                db.flush()
            fb = db.query(Feedback).filter(Feedback.interview_id == intr.id).first()
            if not fb:
                db.add(Feedback(
                    interview_id=intr.id,
                    difficulty_rating=2,
                    rating=3,
                    questions_asked="Basic Java and OOPS",
                    experience_text="Moderate difficulty round with fundamental questions.",
                    topic_analysis="Java",
                    theme="General Preparation"
                ))
                db.flush()
                d6_feedbacks += 1

    # 10. Notifications for admin pagination tests
    admin_u = db.query(User).filter(User.role == "admin").first()
    if admin_u and db.query(Notification).filter(Notification.user_id == admin_u.id).count() < 5:
        for k in range(5):
            db.add(Notification(
                user_id=admin_u.id,
                title=f"System Alert {k+1}",
                message=f"Notification test content {k+1}",
                is_read=False
            ))

    db.commit()

@pytest.fixture(scope="session", autouse=True)
def setup_test_fixtures():
    """Ensure schema tables and minimal test fixtures exist across all test sessions."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_minimal_test_fixtures(db)
    finally:
        db.close()

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def admin_token(db_session):
    admin = db_session.query(User).filter(User.role == "admin").first()
    if not admin:
        seed_minimal_test_fixtures(db_session)
        admin = db_session.query(User).filter(User.role == "admin").first()
    email = admin.email if admin else "admin@college.edu"
    return create_access_token(data={"sub": email, "role": "admin"})

@pytest.fixture(scope="function")
def faculty_token(db_session):
    faculty = db_session.query(User).filter(User.role == "faculty").first()
    if not faculty:
        seed_minimal_test_fixtures(db_session)
        faculty = db_session.query(User).filter(User.role == "faculty").first()
    email = faculty.email if faculty else "faculty.cse@platform.edu"
    return create_access_token(data={"sub": email, "role": "faculty"})

@pytest.fixture(scope="function")
def student_user_and_token(db_session):
    student_user = db_session.query(User).join(Student).first()
    if not student_user:
        seed_minimal_test_fixtures(db_session)
        student_user = db_session.query(User).join(Student).first()
    token = create_access_token(data={"sub": student_user.email, "role": "student"})
    return student_user, token

