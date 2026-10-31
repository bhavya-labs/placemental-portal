import pytest
from datetime import date, timedelta, datetime
from backend.app.models import (
    User, Student, Department, Faculty, Company, PlacementDrive, Application,
    Parent, ParentOTP, Notification, SystemLog, CorrectionRequest
)
from backend.app.routers.parents import sms_provider
from backend.app.auth import create_access_token, get_password_hash
from backend.app.routers.companies import broadcast_drive_notification
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text


def test_drive_notification_idempotency_and_eligibility(client, db_session, admin_token):
    """
    Test 1 & 2:
    - Publishing a drive repeatedly does not generate duplicate notifications.
    - Sends notifications ONLY to eligible students.
    - Subsequent new legitimate drive can generate its own notifications.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    comp = db_session.query(Company).first()
    dept = db_session.query(Department).first()

    # 1. Create a published drive targeting specific criteria
    drive_payload = {
        "company_id": comp.id,
        "role": "Idempotent Test Engineer",
        "package_lpa": 14.5,
        "location": "Hyderabad",
        "cgpa_cutoff": 7.0,
        "allowed_depts": dept.code,
        "allowed_backlogs": 0,
        "interview_date": str(date.today() + timedelta(days=15)),
        "deadline": str(date.today() + timedelta(days=7)),
        "status": "PUBLISHED",
        "batch": "2026"
    }

    resp = client.post("/api/drives", json=drive_payload, headers=headers)
    assert resp.status_code == 200
    drive_id = resp.json()["id"]

    ref_key = f"drive:{drive_id}:published"
    initial_notifs = db_session.query(Notification).filter(Notification.reference_key == ref_key).all()
    initial_count = len(initial_notifs)
    assert initial_count > 0, "Eligible students should receive notifications"

    # Verify that all recipients are indeed eligible
    for n in initial_notifs:
        st = db_session.query(Student).filter(Student.id == n.user_id).first()
        assert st is not None
        assert st.cgpa >= 7.0
        assert st.backlogs == 0
        assert st.department.code == dept.code

    # 2. Update drive multiple times with status PUBLISHED
    for _ in range(3):
        resp_up = client.put(f"/api/drives/{drive_id}", json=drive_payload, headers=headers)
        assert resp_up.status_code == 200

    after_count = db_session.query(Notification).filter(Notification.reference_key == ref_key).count()
    assert after_count == initial_count, f"Duplicate notifications generated! Expected {initial_count}, got {after_count}"

    # 3. Create a separate, new legitimate drive and verify it receives its own notifications
    drive_payload_2 = dict(drive_payload)
    drive_payload_2["role"] = "Second Independent Role"
    resp2 = client.post("/api/drives", json=drive_payload_2, headers=headers)
    assert resp2.status_code == 200
    drive_id_2 = resp2.json()["id"]

    ref_key_2 = f"drive:{drive_id_2}:published"
    notifs_2 = db_session.query(Notification).filter(Notification.reference_key == ref_key_2).all()
    assert len(notifs_2) > 0, "Second drive should generate its own notifications"
    assert drive_id != drive_id_2


def test_safe_drive_deletion_and_archival(client, db_session, admin_token, student_user_and_token):
    """
    Test 3, 4 & 5:
    - Drives with applications CANNOT be hard deleted and are safely ARCHIVED.
    - Historical applications and interview history remain preserved.
    - Archived drives reject new applications.
    """
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_user, student_token = student_user_and_token
    student_headers = {"Authorization": f"Bearer {student_token}"}
    comp = db_session.query(Company).first()
    student = student_user.student_profile

    # Create an active drive
    drive = PlacementDrive(
        company_id=comp.id,
        role="Archival Safety Engineer",
        package_lpa=12.0,
        location="Bengaluru",
        cgpa_cutoff=0.0,
        allowed_depts="ALL",
        allowed_backlogs=10,
        batch=student.batch,
        min_attendance=0.0,
        deadline=date.today() + timedelta(days=5),
        interview_date=date.today() + timedelta(days=10),
        status="Active"
    )
    db_session.add(drive)
    db_session.commit()
    db_session.refresh(drive)

    # Submit an application
    resp_app = client.post("/api/applications", json={"drive_id": drive.id}, headers=student_headers)
    assert resp_app.status_code == 200

    # 1. Attempt to delete drive with application: must ARCHIVE rather than hard-delete
    resp_del = client.delete(f"/api/drives/{drive.id}", headers=admin_headers)
    assert resp_del.status_code == 200
    del_data = resp_del.json()
    assert del_data["archived"] is True
    assert "ARCHIVED" in del_data["status"]

    # Verify drive still exists with status ARCHIVED
    db_session.refresh(drive)
    assert drive.status == "ARCHIVED"

    # Verify application still exists and is accessible
    app_record = db_session.query(Application).filter(Application.drive_id == drive.id).first()
    assert app_record is not None
    assert app_record.student_id == student.id

    # 2. Attempt to submit a new application to the archived drive: must be REJECTED
    resp_new_app = client.post("/api/applications", json={"drive_id": drive.id}, headers=student_headers)
    assert resp_new_app.status_code == 400
    assert "archived" in resp_new_app.json()["detail"].lower()


def test_parent_cannot_associate_arbitrary_phone(client, db_session, student_user_and_token):
    """
    Test 6:
    - Rejects unauthorized phone numbers that are not pre-registered.
    - Prevents arbitrary phone-number association and student account takeover.
    - Does not expose whether student roll number exists.
    """
    student_user, _ = student_user_and_token
    student_id = student_user.id
    fake_phone = "9111122222"

    # Ensure no Parent record exists for this fake phone
    db_session.query(ParentOTP).filter(ParentOTP.mobile_number == fake_phone).delete()
    db_session.query(Parent).filter(Parent.student_id == student_id).delete()
    db_session.commit()

    # Attempt to request OTP with unauthorized phone number
    resp = client.post("/api/parent/request-otp", json={
        "roll_number": student_id,
        "mobile_number": fake_phone
    })
    assert resp.status_code == 400
    assert "unregistered parent mobile number" in resp.json()["detail"].lower()

    # Verify no Parent record was auto-created in database
    parent_check = db_session.query(Parent).filter(Parent.student_id == student_id).first()
    assert parent_check is None, "Parent record must NOT be auto-created for an unverified phone number!"


def test_authorized_parent_registration_and_otp_flow(client, db_session, admin_token, student_user_and_token):
    """
    Test 7:
    - Authorized institutional parent registration.
    - Verified parent can request OTP, receive it via provider, and verify successfully.
    """
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_user, _ = student_user_and_token
    student_id = student_user.id
    verified_phone = "9876599999"

    # Register parent via authorized endpoint
    resp_reg = client.post("/api/parent/register", params={
        "student_id": student_id,
        "parent_name": "Verified Parent",
        "mobile_number": verified_phone,
        "relationship": "Father"
    }, headers=admin_headers)
    assert resp_reg.status_code == 200

    # Request OTP with verified registered number
    resp_otp = client.post("/api/parent/request-otp", json={
        "roll_number": student_id,
        "mobile_number": verified_phone
    })
    assert resp_otp.status_code == 200
    assert resp_otp.json()["success"] is True

    # Retrieve simulated OTP from provider
    dispatched_otp = getattr(sms_provider, "last_dispatched_otp", {}).get(verified_phone)
    assert dispatched_otp is not None

    # Verify OTP
    resp_verify = client.post("/api/parent/verify-otp", json={
        "roll_number": student_id,
        "mobile_number": verified_phone,
        "otp": dispatched_otp
    })
    assert resp_verify.status_code == 200
    assert "access_token" in resp_verify.json()


def test_student_cannot_self_verify(client, db_session, student_user_and_token, faculty_token):
    """
    Test 8 & 9:
    - Students CANNOT self-verify through profile updates.
    - Students CANNOT modify locked academic fields without correction request.
    - Authorized faculty CAN verify student profiles with audit logging.
    """
    student_user, student_token = student_user_and_token
    student_headers = {"Authorization": f"Bearer {student_token}"}
    faculty_headers = {"Authorization": f"Bearer {faculty_token}"}

    student = student_user.student_profile
    student.verification_status = "UNVERIFIED"
    student.profile_completed = False
    original_cgpa = student.cgpa
    db_session.commit()

    # 1. Student updates their own profile (skills, projects, phone)
    resp_update = client.put(f"/api/students/{student.id}", json={
        "phone": "9876543210",
        "skills": "[\"Python\", \"FastAPI\", \"SQL\"]",
        "projects": "[{\"title\": \"Placement Platform\"}]",
        "github_url": "https://github.com/student_test"
    }, headers=student_headers)
    assert resp_update.status_code == 200

    # Verify that verification_status remains UNVERIFIED
    db_session.refresh(student)
    assert student.verification_status == "UNVERIFIED", "Student must NOT be able to self-verify!"
    assert student.profile_completed is True

    # 2. Student attempts to directly alter locked academic field (CGPA)
    resp_tamper = client.put(f"/api/students/{student.id}", json={
        "cgpa": original_cgpa + 1.5,
        "phone": "9876543210"
    }, headers=student_headers)
    assert resp_tamper.status_code == 403
    assert "cannot be modified directly by students" in resp_tamper.json()["detail"].lower()

    # 3. Authorized staff verifies the student profile
    resp_verify = client.put(f"/api/students/{student.id}/verify", json={
        "verification_status": "VERIFIED",
        "remarks": "Academic transcripts verified with registrar records"
    }, headers=faculty_headers)
    assert resp_verify.status_code == 200
    assert resp_verify.json()["verification_status"] == "VERIFIED"

    db_session.refresh(student)
    assert student.verification_status == "VERIFIED"

    # Verify audit log entry
    audit_log = db_session.query(SystemLog).filter(
        SystemLog.action == "VERIFY_STUDENT_PROFILE",
        SystemLog.details.like(f"%Student ID {student.id}%")
    ).first()
    assert audit_log is not None


def test_sqlite_foreign_key_enforcement_on_write(client, db_session):
    """
    Test 11:
    - Validates that SQLite foreign-key enforcement is active on every connection.
    - Inserting an application referencing a non-existent drive raises an IntegrityError.
    """
    student = db_session.query(Student).first()
    non_existent_drive_id = 999999

    orphan_app = Application(
        student_id=student.id,
        drive_id=non_existent_drive_id,
        status="Applied"
    )
    db_session.add(orphan_app)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()


def test_orphan_application_retrieval_defensive(client, db_session, student_user_and_token):
    """
    Test 12:
    - Verifies defensive handling when an application's referenced drive has been deleted (legacy orphan record).
    - Preserves application ID, status, and historical data without raising 500 AttributeError.
    - Returns clear legacy/archived drive labels compatible with frontend types.
    """
    student_user, student_token = student_user_and_token
    student = student_user.student_profile
    headers = {"Authorization": f"Bearer {student_token}"}
    comp = db_session.query(Company).first()

    # Create a real drive and application
    temp_drive = PlacementDrive(
        company_id=comp.id,
        role="Temporary QA Lead",
        package_lpa=16.0,
        location="Remote",
        cgpa_cutoff=0.0,
        allowed_depts="ALL",
        allowed_backlogs=5,
        deadline=date.today() + timedelta(days=10),
        interview_date=date.today() + timedelta(days=15),
        status="Active"
    )
    db_session.add(temp_drive)
    db_session.commit()
    drive_id = temp_drive.id

    orphan_app = Application(
        student_id=student.id,
        drive_id=drive_id,
        status="Applied",
        current_round="Round 1",
        joining_status="Pending",
        remarks="Candidate completed initial test"
    )
    db_session.add(orphan_app)
    db_session.commit()
    app_id = orphan_app.id

    # Simulate legacy drive deletion by temporarily bypassing FK to delete drive row
    db_session.execute(text("PRAGMA foreign_keys = OFF;"))
    db_session.execute(text(f"DELETE FROM placement_drives WHERE id = {drive_id};"))
    db_session.execute(text("PRAGMA foreign_keys = ON;"))
    db_session.commit()

    # Verify drive is deleted but application remains
    deleted_drive_check = db_session.query(PlacementDrive).filter(PlacementDrive.id == drive_id).first()
    assert deleted_drive_check is None, "Drive should be deleted"

    persisted_app = db_session.query(Application).filter(Application.id == app_id).first()
    assert persisted_app is not None, "Application should still exist as an orphan"

    # Query student applications endpoint: MUST return 200 OK and handle missing drive gracefully
    resp = client.get(f"/api/applications/student/{student.id}", headers=headers)
    assert resp.status_code == 200
    app_list = resp.json()

    target_app = next((a for a in app_list if a["id"] == app_id), None)
    assert target_app is not None, "Orphan application must be returned in the list"
    assert target_app["company_name"] == "Archived / Legacy Drive"
    assert target_app["role"] == "N/A"
    assert target_app["package_lpa"] == 0.0
    assert target_app["status"] == "Applied"
    assert target_app["current_round"] == "Round 1"
    assert target_app["remarks"] == "Candidate completed initial test"


def test_active_drives_analytics_filtering(client, db_session, admin_token):
    """
    Test 13:
    - Verifies that active_drives_count counts ONLY active lifecycle statuses:
      ['PUBLISHED', 'REGISTRATION_OPEN', 'Active'].
    - Excludes 'ARCHIVED', 'DRAFT', 'CANCELLED', 'COMPLETED'.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    comp = db_session.query(Company).first()

    # Clear non-fixture drives for clear deterministic counting
    active_statuses = ["PUBLISHED", "REGISTRATION_OPEN", "Active"]
    all_test_statuses = [
        "PUBLISHED", "REGISTRATION_OPEN", "Active",
        "ARCHIVED", "DRAFT", "CANCELLED", "COMPLETED"
    ]

    initial_active_count = db_session.query(PlacementDrive).filter(PlacementDrive.status.in_(active_statuses)).count()
    initial_total_count = db_session.query(PlacementDrive).count()

    # Create 1 drive for each status
    created_drives = []
    for st in all_test_statuses:
        d = PlacementDrive(
            company_id=comp.id,
            role=f"Role for {st}",
            package_lpa=10.0,
            location="City",
            cgpa_cutoff=6.0,
            allowed_depts="ALL",
            allowed_backlogs=0,
            deadline=date.today() + timedelta(days=10),
            interview_date=date.today() + timedelta(days=15),
            status=st
        )
        db_session.add(d)
        created_drives.append(d)
    db_session.commit()

    resp = client.get("/api/analytics/dashboard", headers=headers)
    assert resp.status_code == 200
    analytics_data = resp.json()

    expected_active = initial_active_count + 3  # Only PUBLISHED, REGISTRATION_OPEN, Active
    assert analytics_data["active_drives_count"] == expected_active, (
        f"Expected {expected_active} active drives, got {analytics_data['active_drives_count']}"
    )


def test_parent_registration_department_authorization(client, db_session, admin_token):
    """
    Test 14:
    - Admin & TPO retain global scope.
    - Faculty and HOD are strictly department-scoped.
    - Cross-department registration returns 403.
    - Faculty without department returns 403.
    - Student cannot register for another student (403).
    - Student can register parent contact for their own profile (200).
    """
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    shared_pwd = get_password_hash("password123")

    depts = {d.code: d for d in db_session.query(Department).all()}
    cse_dept = depts["CSE"]
    ece_dept = depts.get("ECE")
    if not ece_dept:
        ece_dept = Department(name="Electronics and Communication", code="ECE")
        db_session.add(ece_dept)
        db_session.flush()

    # 1. Create CSE Student and ECE Student
    u_cse = User(email="student.cse.parent@college.edu", name="CSE Student", role="student", password_hash=shared_pwd)
    u_ece = User(email="student.ece.parent@college.edu", name="ECE Student", role="student", password_hash=shared_pwd)
    db_session.add_all([u_cse, u_ece])
    db_session.flush()

    s_cse = Student(id=u_cse.id, dept_id=cse_dept.id, gender="M", batch="2026", cgpa=8.0, attendance=85.0, backlogs=0)
    s_ece = Student(id=u_ece.id, dept_id=ece_dept.id, gender="F", batch="2026", cgpa=8.5, attendance=90.0, backlogs=0)
    db_session.add_all([s_cse, s_ece])
    db_session.flush()

    # 2. Create Faculty (CSE), HOD (CSE), unassigned Faculty, and TPO
    u_fac_cse = User(email="fac.cse.coord@college.edu", name="CSE Coordinator", role="faculty", password_hash=shared_pwd)
    u_hod_cse = User(email="hod.cse.coord@college.edu", name="CSE HOD", role="hod", password_hash=shared_pwd)
    u_fac_none = User(email="fac.unassigned@college.edu", name="Unassigned Faculty", role="faculty", password_hash=shared_pwd)
    u_tpo = User(email="tpo.officer@college.edu", name="TPO Officer", role="tpo", password_hash=shared_pwd)
    db_session.add_all([u_fac_cse, u_hod_cse, u_fac_none, u_tpo])
    db_session.flush()

    db_session.add(Faculty(id=u_fac_cse.id, dept_id=cse_dept.id, designation="Assistant Professor"))
    db_session.add(Faculty(id=u_hod_cse.id, dept_id=cse_dept.id, designation="HOD"))
    db_session.commit()

    fac_cse_token = create_access_token(data={"sub": u_fac_cse.email, "role": "faculty"})
    hod_cse_token = create_access_token(data={"sub": u_hod_cse.email, "role": "hod"})
    fac_none_token = create_access_token(data={"sub": u_fac_none.email, "role": "faculty"})
    tpo_token = create_access_token(data={"sub": "tpo.officer@college.edu", "role": "tpo"})
    student_cse_token = create_access_token(data={"sub": u_cse.email, "role": "student"})

    fac_cse_headers = {"Authorization": f"Bearer {fac_cse_token}"}
    hod_cse_headers = {"Authorization": f"Bearer {hod_cse_token}"}
    fac_none_headers = {"Authorization": f"Bearer {fac_none_token}"}
    tpo_headers = {"Authorization": f"Bearer {tpo_token}"}
    student_cse_headers = {"Authorization": f"Bearer {student_cse_token}"}

    # Verify 1: Admin can register parent for CSE student -> 200
    r_admin = client.post("/api/parent/register", params={
        "student_id": s_cse.id, "parent_name": "Admin Registered Parent", "mobile_number": "9123450001"
    }, headers=admin_headers)
    assert r_admin.status_code == 200

    # Verify 2: TPO can register parent for ECE student -> 200 (global scope)
    r_tpo = client.post("/api/parent/register", params={
        "student_id": s_ece.id, "parent_name": "TPO Registered Parent", "mobile_number": "9123450002"
    }, headers=tpo_headers)
    assert r_tpo.status_code == 200

    # Verify 3: Faculty CSE can register parent for CSE student (same department) -> 200
    r_fac_in = client.post("/api/parent/register", params={
        "student_id": s_cse.id, "parent_name": "Faculty Registered Parent", "mobile_number": "9123450003"
    }, headers=fac_cse_headers)
    assert r_fac_in.status_code == 200

    # Verify 4: Faculty CSE attempting cross-department registration for ECE student -> 403
    r_fac_cross = client.post("/api/parent/register", params={
        "student_id": s_ece.id, "parent_name": "Malicious Faculty Parent", "mobile_number": "9123450004"
    }, headers=fac_cse_headers)
    assert r_fac_cross.status_code == 403
    assert "assigned department" in r_fac_cross.json()["detail"].lower()

    # Verify 5: HOD CSE attempting cross-department registration for ECE student -> 403
    r_hod_cross = client.post("/api/parent/register", params={
        "student_id": s_ece.id, "parent_name": "Malicious HOD Parent", "mobile_number": "9123450005"
    }, headers=hod_cse_headers)
    assert r_hod_cross.status_code == 403
    assert "assigned department" in r_hod_cross.json()["detail"].lower()

    # Verify 6: Faculty with no department profile attempting registration -> 403
    r_fac_none = client.post("/api/parent/register", params={
        "student_id": s_cse.id, "parent_name": "Unassigned Parent", "mobile_number": "9123450006"
    }, headers=fac_none_headers)
    assert r_fac_none.status_code == 403
    assert "no assigned department" in r_fac_none.json()["detail"].lower()

    # Verify 7: Student CSE attempting to register parent for Student ECE -> 403
    r_stu_other = client.post("/api/parent/register", params={
        "student_id": s_ece.id, "parent_name": "Impersonator Parent", "mobile_number": "9123450007"
    }, headers=student_cse_headers)
    assert r_stu_other.status_code == 403
    assert "own profile" in r_stu_other.json()["detail"].lower()

    # Verify 8: Student CSE registering parent for their own profile -> 200
    r_stu_self = client.post("/api/parent/register", params={
        "student_id": s_cse.id, "parent_name": "Self Registered Parent", "mobile_number": "9123450008"
    }, headers=student_cse_headers)
    assert r_stu_self.status_code == 200


def test_notification_concurrency_and_partial_unique_index(client, db_session):
    """
    Test 15:
    - Direct validation of partial unique index uq_notif_user_ref on (user_id, reference_key).
    - Prevents duplicate non-null reference keys for the same user.
    - Allows multiple NULL reference keys for the same user (unrelated notifications).
    - Allows identical reference keys for different users.
    - Validates that broadcast_drive_notification uses savepoints to gracefully absorb conflicts.
    """
    u = db_session.query(User).filter(User.role == "student").first()
    u2 = db_session.query(User).filter(User.role == "student", User.id != u.id).first()

    ref_key = f"test:partial_unique:{datetime.utcnow().timestamp()}"

    # 1. Insert first notification with reference_key
    n1 = Notification(
        user_id=u.id,
        title="Event 1",
        message="Message 1",
        reference_key=ref_key
    )
    db_session.add(n1)
    db_session.commit()

    # 2. Attempt duplicate insert for SAME user and SAME reference_key -> MUST raise IntegrityError
    n1_dup = Notification(
        user_id=u.id,
        title="Event 1 Duplicate",
        message="Message 1 Duplicate",
        reference_key=ref_key
    )
    db_session.add(n1_dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 3. Insert notification with SAME reference_key for DIFFERENT user -> Allowed
    n2 = Notification(
        user_id=u2.id,
        title="Event 1",
        message="Message 1",
        reference_key=ref_key
    )
    db_session.add(n2)
    db_session.commit()
    assert n2.id is not None

    # 4. Insert multiple notifications with NULL reference_key for user -> Allowed (partial index)
    null_notif_1 = Notification(user_id=u.id, title="Alert 1", message="General alert", reference_key=None)
    null_notif_2 = Notification(user_id=u.id, title="Alert 2", message="General alert", reference_key=None)
    db_session.add_all([null_notif_1, null_notif_2])
    db_session.commit()
    assert null_notif_1.id is not None
    assert null_notif_2.id is not None

    # 5. Test savepoint conflict absorption in broadcast_drive_notification
    comp = db_session.query(Company).first()
    drive = PlacementDrive(
        company_id=comp.id,
        role="Concurrency Test Role",
        package_lpa=11.0,
        location="Remote",
        cgpa_cutoff=0.0,
        allowed_depts="ALL",
        allowed_backlogs=5,
        deadline=date.today() + timedelta(days=10),
        interview_date=date.today() + timedelta(days=15),
        status="PUBLISHED"
    )
    db_session.add(drive)
    db_session.commit()

    broadcast_ref = f"drive:{drive.id}:published"
    count1 = broadcast_drive_notification(db_session, drive, "Drive Published", "Msg", broadcast_ref)
    assert count1 > 0

    # Second call for the same broadcast: must complete safely without raising an error
    count2 = broadcast_drive_notification(db_session, drive, "Drive Published", "Msg", broadcast_ref)
    assert count2 == 0

