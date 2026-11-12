import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.models import (
    Base, User, Student, Department, Company, PlacementDrive, Application, 
    PlacementActivity, Interview, Feedback, SystemLog
)
from backend.app.schemas import (
    PlacementDriveCreate, ApplicationCreate, ApplicationStatusUpdate
)
from backend.app.routers.companies import (
    get_drives, get_drive_details, update_drive, delete_drive, archive_drive,
    get_ist_date, IST_TIMEZONE, STATUS_DRAFT, STATUS_SCHEDULED,
    STATUS_REGISTRATION_OPEN, STATUS_REGISTRATION_CLOSED, STATUS_ONGOING,
    STATUS_COMPLETED, STATUS_ARCHIVED
)
from backend.app.routers.applications import (
    apply_to_drive, withdraw_application, get_student_applications, update_application_status
)

@pytest.fixture(scope="module")
def isolated_db():
    engine = create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed Departments
    cse = Department(id=1, name="Computer Science & Engineering", code="CSE")
    ece = Department(id=2, name="Electronics & Communication", code="ECE")
    session.add_all([cse, ece])
    session.commit()

    # Seed Users
    admin_u = User(id=1, email="admin@institution.edu", name="System Admin", role="admin", password_hash="hash")
    std1_u = User(id=2, email="student1@institution.edu", name="Aarav Sharma", role="student", password_hash="hash")
    std2_u = User(id=3, email="student2@institution.edu", name="Diya Patel", role="student", password_hash="hash")
    session.add_all([admin_u, std1_u, std2_u])
    session.commit()

    # Seed Students
    s1 = Student(
        id=2, dept_id=1, gender="Male", batch="2026", section="A",
        phone="9876543210", cgpa=8.5, backlogs=0, attendance=85.0,
        status="Unplaced", skills='["Python", "FastAPI"]'
    )
    s2 = Student(
        id=3, dept_id=1, gender="Female", batch="2026", section="A",
        phone="9876543211", cgpa=7.0, backlogs=1, attendance=70.0,
        status="Unplaced", skills='["Java"]'
    )
    session.add_all([s1, s2])
    session.commit()

    # Seed Company
    comp = Company(id=1, name="TechCorp Global", industry="Technology", website="https://techcorp.example.com")
    session.add(comp)
    session.commit()

    return {
        "session": session,
        "admin": admin_u,
        "student1_user": std1_u,
        "student1_profile": s1,
        "student2_user": std2_u,
        "student2_profile": s2,
        "company": comp
    }


def test_drive_archival_with_applications_preserves_records(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]
    student = isolated_db["student1_profile"]

    today = get_ist_date()
    drive = PlacementDrive(
        id=101,
        company_id=1,
        role="Backend Engineer",
        package_lpa=12.0,
        location="Bengaluru",
        cgpa_cutoff=7.0,
        allowed_depts="CSE,ECE",
        allowed_backlogs=0,
        interview_date=today + timedelta(days=14),
        deadline=today + timedelta(days=7),
        status="REGISTRATION_OPEN",
        batch="2026",
        min_attendance=75.0
    )
    session.add(drive)
    session.commit()

    app = Application(
        id=501,
        student_id=student.id,
        drive_id=drive.id,
        status="Applied",
        current_round="Round 1"
    )
    session.add(app)
    session.commit()

    # Admin attempts deletion
    res = delete_drive(drive_id=drive.id, current_user=admin, db=session)

    assert res["archived"] is True
    assert res["status"] == "ARCHIVED"
    assert res["applications_preserved"] == 1
    assert "safely ARCHIVED" in res["message"]

    # Verify drive still exists with ARCHIVED status
    refreshed_drive = session.query(PlacementDrive).filter(PlacementDrive.id == drive.id).first()
    assert refreshed_drive is not None
    assert refreshed_drive.status == "ARCHIVED"

    # Verify application remains intact
    refreshed_app = session.query(Application).filter(Application.id == app.id).first()
    assert refreshed_app is not None
    assert refreshed_app.drive_id == drive.id


def test_drive_archival_with_activities_preserves_records(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]

    today = get_ist_date()
    drive = PlacementDrive(
        id=102,
        company_id=1,
        role="DevOps Engineer",
        package_lpa=10.0,
        location="Hyderabad",
        cgpa_cutoff=6.5,
        allowed_depts="ALL",
        allowed_backlogs=1,
        interview_date=today + timedelta(days=20),
        deadline=today + timedelta(days=10),
        status="REGISTRATION_OPEN",
        batch="2026",
        min_attendance=70.0
    )
    session.add(drive)
    session.commit()

    activity = PlacementActivity(
        id=701,
        placement_drive_id=drive.id,
        company_id=drive.company_id,
        activity_name="Pre-Placement Talk",
        activity_type="PPT",
        date=today,
        start_time="10:00",
        end_time="11:00",
        location="Auditorium",
        mandatory=True
    )
    session.add(activity)
    session.commit()

    res = delete_drive(drive_id=drive.id, current_user=admin, db=session)
    assert res["archived"] is True
    assert res["status"] == "ARCHIVED"
    assert res["activities_preserved"] == 1

    refreshed_act = session.query(PlacementActivity).filter(PlacementActivity.id == activity.id).first()
    assert refreshed_act is not None
    assert refreshed_act.placement_drive_id == drive.id


def test_drive_hard_deletion_with_zero_records(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]

    today = get_ist_date()
    drive = PlacementDrive(
        id=103,
        company_id=1,
        role="Data Scientist (Cancelled)",
        package_lpa=15.0,
        location="Pune",
        cgpa_cutoff=8.0,
        allowed_depts="CSE",
        allowed_backlogs=0,
        interview_date=today + timedelta(days=30),
        deadline=today + timedelta(days=15),
        status="DRAFT",
        batch="2026",
        min_attendance=75.0
    )
    session.add(drive)
    session.commit()

    res = delete_drive(drive_id=drive.id, current_user=admin, db=session)
    assert res["archived"] is False
    assert "deleted successfully" in res["message"]

    deleted_drive = session.query(PlacementDrive).filter(PlacementDrive.id == drive.id).first()
    assert deleted_drive is None


def test_historical_data_preservation(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]
    student = isolated_db["student1_profile"]

    today = get_ist_date()
    drive = PlacementDrive(
        id=104,
        company_id=1,
        role="Product Engineer",
        package_lpa=14.0,
        location="Gurugram",
        cgpa_cutoff=7.5,
        allowed_depts="CSE",
        allowed_backlogs=0,
        interview_date=today + timedelta(days=10),
        deadline=today + timedelta(days=3),
        status="REGISTRATION_CLOSED",
        batch="2026",
        min_attendance=75.0
    )
    session.add(drive)
    session.commit()

    app = Application(
        id=504,
        student_id=student.id,
        drive_id=drive.id,
        status="Shortlisted",
        current_round="Technical Round"
    )
    session.add(app)
    session.commit()

    interview = Interview(
        id=601,
        application_id=app.id,
        student_id=student.id,
        round_name="Technical Round 1",
        status="Scheduled",
        interview_date=datetime.now() + timedelta(days=2)
    )
    session.add(interview)
    session.commit()

    feedback = Feedback(
        id=801,
        interview_id=interview.id,
        experience_text="Great technical discussion on system design and trees.",
        difficulty_rating=4
    )
    session.add(feedback)
    session.commit()

    # Call archive endpoint
    arch_res = archive_drive(drive_id=drive.id, current_user=admin, db=session)
    assert arch_res["status"] == "ARCHIVED"
    assert arch_res["applications_count"] == 1

    # Verify interview and feedback records remain completely intact
    assert session.query(Application).filter(Application.id == 504).first() is not None
    assert session.query(Interview).filter(Interview.id == 601).first() is not None
    assert session.query(Feedback).filter(Feedback.id == 801).first() is not None


def test_default_get_drives_excludes_archived(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]

    drives = get_drives(status_filter=None, current_user=admin, db=session)
    drive_ids = [d["id"] for d in drives]
    statuses = [d["status"] for d in drives]

    # Archived drive 101 must NOT be in the default list
    assert 101 not in drive_ids
    assert "ARCHIVED" not in statuses


def test_get_drives_with_archived_filter(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]

    drives = get_drives(status_filter="ARCHIVED", current_user=admin, db=session)
    drive_ids = [d["id"] for d in drives]

    assert 101 in drive_ids
    assert 102 in drive_ids
    assert 104 in drive_ids
    for d in drives:
        assert d["status"] == "ARCHIVED"
        assert d["is_archived"] is True
        assert d["effective_status"] == "ARCHIVED"


def test_scheduled_drives_visibility_and_application_rejection(isolated_db):
    session = isolated_db["session"]
    student_user = isolated_db["student1_user"]
    student_profile = isolated_db["student1_profile"]

    today = get_ist_date()
    drive = PlacementDrive(
        id=105,
        company_id=1,
        role="Future Analyst",
        package_lpa=8.0,
        location="Noida",
        cgpa_cutoff=7.0,
        allowed_depts="CSE",
        allowed_backlogs=0,
        interview_date=today + timedelta(days=60),
        deadline=today + timedelta(days=45),
        status="SCHEDULED",
        batch="2026",
        min_attendance=75.0
    )
    session.add(drive)
    session.commit()

    # Student views drives list
    student_drives = get_drives(status_filter=None, current_user=student_user, db=session)
    scheduled_drives = [d for d in student_drives if d["id"] == 105]
    assert len(scheduled_drives) == 1
    assert scheduled_drives[0]["status"] == "SCHEDULED"
    assert scheduled_drives[0]["effective_status"] == "SCHEDULED"
    assert scheduled_drives[0]["is_registration_open"] is False

    # Student attempts to apply to scheduled drive
    with pytest.raises(HTTPException) as exc_info:
        apply_to_drive(
            app_data=ApplicationCreate(drive_id=105),
            current_student=student_profile,
            db=session
        )
    assert exc_info.value.status_code == 400
    assert "Registration for this scheduled drive is not yet open" in exc_info.value.detail


def test_registration_open_and_closed_boundaries_in_ist(isolated_db):
    session = isolated_db["session"]
    student_profile = isolated_db["student1_profile"]
    student2_profile = isolated_db["student2_profile"]

    today_ist = get_ist_date()

    # Drive 106: Deadline is TODAY in IST (Application must be accepted)
    drive_today = PlacementDrive(
        id=106,
        company_id=1,
        role="Deadline Today Role",
        package_lpa=9.0,
        location="Remote",
        cgpa_cutoff=7.0,
        allowed_depts="CSE",
        allowed_backlogs=0,
        interview_date=today_ist + timedelta(days=7),
        deadline=today_ist,
        status="REGISTRATION_OPEN",
        batch="2026",
        min_attendance=75.0
    )
    session.add(drive_today)

    # Drive 107: Deadline was YESTERDAY in IST (Application must be rejected)
    drive_yesterday = PlacementDrive(
        id=107,
        company_id=1,
        role="Deadline Yesterday Role",
        package_lpa=9.0,
        location="Remote",
        cgpa_cutoff=6.5,
        allowed_depts="CSE",
        allowed_backlogs=2,
        interview_date=today_ist + timedelta(days=7),
        deadline=today_ist - timedelta(days=1),
        status="REGISTRATION_OPEN",
        batch="2026",
        min_attendance=65.0
    )
    session.add(drive_yesterday)
    session.commit()

    # 1. Applying on deadline day succeeds
    res = apply_to_drive(
        app_data=ApplicationCreate(drive_id=106),
        current_student=student_profile,
        db=session
    )
    assert "Application submitted successfully" in res["message"]

    # 2. Applying after deadline day fails with deadline error
    with pytest.raises(HTTPException) as exc_info:
        apply_to_drive(
            app_data=ApplicationCreate(drive_id=107),
            current_student=student2_profile,
            db=session
        )
    assert exc_info.value.status_code == 400
    assert "Application deadline has passed" in exc_info.value.detail


def test_ongoing_and_completed_drive_handling(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]

    today = get_ist_date()
    # Past interview date alone must NOT mark drive completed
    drive = PlacementDrive(
        id=108,
        company_id=1,
        role="Ongoing Evaluations Role",
        package_lpa=11.0,
        location="Bengaluru",
        cgpa_cutoff=7.0,
        allowed_depts="CSE",
        allowed_backlogs=0,
        interview_date=today - timedelta(days=5),
        deadline=today - timedelta(days=10),
        status="ONGOING",
        batch="2026",
        min_attendance=75.0
    )
    session.add(drive)
    session.commit()

    drives = get_drives(status_filter=None, current_user=admin, db=session)
    target = [d for d in drives if d["id"] == 108][0]

    # Effective status remains ONGOING; NOT marked COMPLETED automatically
    assert target["effective_status"] == "ONGOING"
    assert target["status"] == "ONGOING"


def test_student_access_restrictions(isolated_db):
    session = isolated_db["session"]
    student_user = isolated_db["student2_user"]

    # 1. Student cannot inspect DRAFT drive details
    today = get_ist_date()
    draft_drive = PlacementDrive(
        id=109,
        company_id=1,
        role="Secret Internal Draft Role",
        package_lpa=20.0,
        location="Remote",
        cgpa_cutoff=7.0,
        allowed_depts="CSE",
        allowed_backlogs=0,
        interview_date=today + timedelta(days=20),
        deadline=today + timedelta(days=10),
        status="DRAFT",
        batch="2026",
        min_attendance=75.0
    )
    session.add(draft_drive)
    session.commit()

    with pytest.raises(HTTPException) as exc_info:
        get_drive_details(drive_id=109, current_user=student_user, db=session)
    assert exc_info.value.status_code == 404

    # 2. Student cannot inspect ARCHIVED drive details if they haven't applied
    with pytest.raises(HTTPException) as exc_info:
        get_drive_details(drive_id=102, current_user=student_user, db=session)
    assert exc_info.value.status_code == 404

    # 3. Student querying status_filter="ARCHIVED" receives empty list
    student_archived = get_drives(status_filter="ARCHIVED", current_user=student_user, db=session)
    assert len(student_archived) == 0


def test_ist_date_boundary_midnight():
    # Verify get_ist_date returns current date in UTC+05:30
    utc_now = datetime.now(timezone.utc)
    ist_now = datetime.now(IST_TIMEZONE)
    assert get_ist_date() == ist_now.date()

    # Calculate difference between UTC date and IST date
    # In the window between 18:30 UTC and 23:59 UTC, IST is already on the next calendar day
    mock_utc_late_evening = datetime(2026, 9, 15, 20, 0, 0, tzinfo=timezone.utc)
    mock_ist = mock_utc_late_evening.astimezone(IST_TIMEZONE)
    assert mock_utc_late_evening.date() == date(2026, 9, 15)
    assert mock_ist.date() == date(2026, 9, 16)


def test_legacy_orphan_application_1253_preserved(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]
    student = isolated_db["student1_profile"]

    # Seed legacy orphan application referencing non-existent drive_id (182)
    session.execute(text("PRAGMA foreign_keys = OFF"))
    orphan_app = Application(
        id=1253,
        student_id=student.id,
        drive_id=182,
        status="Applied",
        current_round="Review",
        joining_status="Pending"
    )
    session.add(orphan_app)
    session.commit()
    session.execute(text("PRAGMA foreign_keys = ON"))

    # 1. Listing applications handles orphan application cleanly with fallback name
    apps = get_student_applications(student_id=student.id, current_user=admin, db=session)
    target = [a for a in apps if a["id"] == 1253]
    assert len(target) == 1
    assert target[0]["company_name"] == "Archived / Legacy Drive"
    assert target[0]["role"] == "N/A"

    # 2. Updating status on orphan application does not throw AttributeError
    status_update = ApplicationStatusUpdate(
        status="Selected",
        current_round="Final Offer",
        joining_status="Accepted",
        remarks="Legacy record preserved"
    )
    res = update_application_status(
        application_id=1253,
        status_data=status_update,
        current_user=admin,
        db=session
    )
    assert "Application status updated" in res["message"]

    refreshed_orphan = session.query(Application).filter(Application.id == 1253).first()
    assert refreshed_orphan is not None
    assert refreshed_orphan.id == 1253
    assert refreshed_orphan.status == "Selected"


def test_lifecycle_status_transitions(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]

    today = get_ist_date()
    drive = PlacementDrive(
        id=110,
        company_id=1,
        role="Lifecycle Transition Role",
        package_lpa=10.0,
        location="Bengaluru",
        cgpa_cutoff=7.0,
        allowed_depts="CSE",
        allowed_backlogs=0,
        interview_date=today + timedelta(days=20),
        deadline=today + timedelta(days=10),
        status="DRAFT",
        batch="2026",
        min_attendance=75.0
    )
    session.add(drive)
    session.commit()

    # Transition 1: DRAFT -> SCHEDULED
    update_data = PlacementDriveCreate(
        company_id=1, role="Lifecycle Transition Role", package_lpa=10.0,
        location="Bengaluru", cgpa_cutoff=7.0, allowed_depts="CSE", allowed_backlogs=0,
        interview_date=today + timedelta(days=20), deadline=today + timedelta(days=10),
        status="SCHEDULED", batch="2026", min_attendance=75.0
    )
    res = update_drive(drive_id=110, drive_data=update_data, current_user=admin, db=session)
    assert res["status"] == "SCHEDULED"

    # Transition 2: SCHEDULED -> REGISTRATION_OPEN
    update_data.status = "REGISTRATION_OPEN"
    res = update_drive(drive_id=110, drive_data=update_data, current_user=admin, db=session)
    assert res["status"] == "REGISTRATION_OPEN"

    # Transition 3: REGISTRATION_OPEN -> REGISTRATION_CLOSED
    update_data.status = "REGISTRATION_CLOSED"
    res = update_drive(drive_id=110, drive_data=update_data, current_user=admin, db=session)
    assert res["status"] == "REGISTRATION_CLOSED"

    # Transition 4: REGISTRATION_CLOSED -> ONGOING
    update_data.status = "ONGOING"
    res = update_drive(drive_id=110, drive_data=update_data, current_user=admin, db=session)
    assert res["status"] == "ONGOING"

    # Transition 5: ONGOING -> COMPLETED
    update_data.status = "COMPLETED"
    res = update_drive(drive_id=110, drive_data=update_data, current_user=admin, db=session)
    assert res["status"] == "COMPLETED"

    # Transition 6: COMPLETED -> ARCHIVED
    update_data.status = "ARCHIVED"
    res = update_drive(drive_id=110, drive_data=update_data, current_user=admin, db=session)
    assert res["status"] == "ARCHIVED"

    # Invalid Transition: ARCHIVED -> INVALID_STATUS raises 400
    update_data.status = "NON_EXISTENT_STATUS"
    with pytest.raises(HTTPException) as exc_info:
        update_drive(drive_id=110, drive_data=update_data, current_user=admin, db=session)
    assert exc_info.value.status_code == 400
    assert "Invalid lifecycle status transition" in exc_info.value.detail
