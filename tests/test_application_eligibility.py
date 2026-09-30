import pytest
from datetime import date, timedelta
from backend.app.models import PlacementDrive, Company, Application, Student, User, Department
from backend.app.auth import create_access_token

def test_drive_not_found(client, student_user_and_token):
    student_user, token = student_user_and_token
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/applications", json={"drive_id": 999999}, headers=headers)
    assert resp.status_code == 404
    assert "Placement drive not found" in resp.json()["detail"]

def test_eligibility_deadline_passed(client, db_session, student_user_and_token):
    student_user, token = student_user_and_token
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create drive with expired deadline
    comp = db_session.query(Company).first()
    drive = PlacementDrive(
        company_id=comp.id,
        role="Expired Role QA",
        package_lpa=10.0,
        location="Remote",
        cgpa_cutoff=5.0,
        allowed_depts="ALL",
        allowed_backlogs=5,
        deadline=date.today() - timedelta(days=2),
        interview_date=date.today() - timedelta(days=1),
        status="Active"
    )
    db_session.add(drive)
    db_session.commit()
    db_session.refresh(drive)

    resp = client.post("/api/applications", json={"drive_id": drive.id}, headers=headers)
    assert resp.status_code == 400
    assert "Application deadline has passed" in resp.json()["detail"]

def test_eligibility_department_mismatch(client, db_session, student_user_and_token):
    student_user, token = student_user_and_token
    headers = {"Authorization": f"Bearer {token}"}
    student = student_user.student_profile

    # Allowed dept is something other than student's dept
    other_code = "CIVIL" if student.department.code != "CIVIL" else "MECH"
    comp = db_session.query(Company).first()
    drive = PlacementDrive(
        company_id=comp.id,
        role="Dept Specific Role",
        package_lpa=8.0,
        location="Bengaluru",
        cgpa_cutoff=1.0,
        allowed_depts=other_code,
        allowed_backlogs=10,
        batch=student.batch,
        deadline=date.today() + timedelta(days=5),
        interview_date=date.today() + timedelta(days=10),
        status="Active"
    )
    db_session.add(drive)
    db_session.commit()
    db_session.refresh(drive)

    resp = client.post("/api/applications", json={"drive_id": drive.id}, headers=headers)
    assert resp.status_code == 400
    assert "not eligible for this drive" in resp.json()["detail"]

def test_eligibility_cgpa_cutoff(client, db_session, student_user_and_token):
    student_user, token = student_user_and_token
    headers = {"Authorization": f"Bearer {token}"}
    student = student_user.student_profile

    comp = db_session.query(Company).first()
    drive = PlacementDrive(
        company_id=comp.id,
        role="High CGPA Role",
        package_lpa=25.0,
        location="Hyderabad",
        cgpa_cutoff=student.cgpa + 1.5,  # Higher than student's CGPA
        allowed_depts="ALL",
        allowed_backlogs=10,
        batch=student.batch,
        deadline=date.today() + timedelta(days=5),
        interview_date=date.today() + timedelta(days=10),
        status="Active"
    )
    db_session.add(drive)
    db_session.commit()
    db_session.refresh(drive)

    resp = client.post("/api/applications", json={"drive_id": drive.id}, headers=headers)
    assert resp.status_code == 400
    assert "below the required cutoff" in resp.json()["detail"]

def test_eligibility_backlogs_exceeded(client, db_session, student_user_and_token):
    student_user, token = student_user_and_token
    headers = {"Authorization": f"Bearer {token}"}
    student = student_user.student_profile

    # Temporarily set student backlogs to 2 if 0
    orig_backlogs = student.backlogs
    student.backlogs = 3
    db_session.commit()

    try:
        comp = db_session.query(Company).first()
        drive = PlacementDrive(
            company_id=comp.id,
            role="Zero Backlogs Only",
            package_lpa=12.0,
            location="Pune",
            cgpa_cutoff=0.0,
            allowed_depts="ALL",
            allowed_backlogs=0,  # Strict zero backlogs
            batch=student.batch,
            deadline=date.today() + timedelta(days=5),
            interview_date=date.today() + timedelta(days=10),
            status="Active"
        )
        db_session.add(drive)
        db_session.commit()
        db_session.refresh(drive)

        resp = client.post("/api/applications", json={"drive_id": drive.id}, headers=headers)
        assert resp.status_code == 400
        assert "exceed the allowed limit" in resp.json()["detail"]
    finally:
        student.backlogs = orig_backlogs
        db_session.commit()

def test_eligibility_batch_mismatch(client, db_session, student_user_and_token):
    student_user, token = student_user_and_token
    headers = {"Authorization": f"Bearer {token}"}
    student = student_user.student_profile

    comp = db_session.query(Company).first()
    drive = PlacementDrive(
        company_id=comp.id,
        role="Different Batch Drive",
        package_lpa=6.0,
        location="Noida",
        cgpa_cutoff=0.0,
        allowed_depts="ALL",
        allowed_backlogs=10,
        batch="1999",  # Non-matching batch
        deadline=date.today() + timedelta(days=5),
        interview_date=date.today() + timedelta(days=10),
        status="Active"
    )
    db_session.add(drive)
    db_session.commit()
    db_session.refresh(drive)

    resp = client.post("/api/applications", json={"drive_id": drive.id}, headers=headers)
    assert resp.status_code == 400
    assert "does not match the drive criteria" in resp.json()["detail"]

def test_eligibility_attendance_minimum(client, db_session, student_user_and_token):
    student_user, token = student_user_and_token
    headers = {"Authorization": f"Bearer {token}"}
    student = student_user.student_profile

    comp = db_session.query(Company).first()
    drive = PlacementDrive(
        company_id=comp.id,
        role="High Attendance Drive",
        package_lpa=9.0,
        location="Chennai",
        cgpa_cutoff=0.0,
        allowed_depts="ALL",
        allowed_backlogs=10,
        batch=student.batch,
        min_attendance=99.9,  # Unattainable attendance threshold
        deadline=date.today() + timedelta(days=5),
        interview_date=date.today() + timedelta(days=10),
        status="Active"
    )
    db_session.add(drive)
    db_session.commit()
    db_session.refresh(drive)

    resp = client.post("/api/applications", json={"drive_id": drive.id}, headers=headers)
    assert resp.status_code == 400
    assert "below the required minimum" in resp.json()["detail"]

def test_successful_application_and_duplicate_check(client, db_session, student_user_and_token):
    student_user, token = student_user_and_token
    headers = {"Authorization": f"Bearer {token}"}
    student = student_user.student_profile

    comp = db_session.query(Company).first()
    drive = PlacementDrive(
        company_id=comp.id,
        role="Valid QA Drive",
        package_lpa=11.0,
        location="Remote",
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

    # 1. First submission succeeds
    resp1 = client.post("/api/applications", json={"drive_id": drive.id}, headers=headers)
    assert resp1.status_code == 200
    assert "Application submitted successfully" in resp1.json()["message"]

    # 2. Duplicate submission fails
    resp2 = client.post("/api/applications", json={"drive_id": drive.id}, headers=headers)
    assert resp2.status_code == 400
    assert "already applied for this drive" in resp2.json()["detail"]
