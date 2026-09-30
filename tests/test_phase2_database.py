import os
import sys
import sqlite3
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User, Notification, Company, Student, Department
from backend.app.auth import create_access_token

def test_alembic_revision():
    print("\n--- Test 1: Alembic Revision ---")
    conn = sqlite3.connect(str(project_root / "placement_portal.db"))
    cur = conn.cursor()
    cur.execute("SELECT version_num FROM alembic_version")
    row = cur.fetchone()
    print(f"Current Alembic revision in DB: {row[0] if row else 'None'}")
    assert row is not None, "Alembic version table is empty!"
    assert row[0] in ["6e105b4276ae", "ac9fcc9ba19f"], f"Expected head revision 6e105b4276ae or ac9fcc9ba19f, got {row[0]}"
    print(f"PASS: Alembic head revision is confirmed ({row[0]}).")

def test_database_indexes():
    print("\n--- Test 2: Database Indexes Verification ---")
    conn = sqlite3.connect(str(project_root / "placement_portal.db"))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cur.fetchall()}
    
    expected_indexes = [
        "ix_users_role",
        "ix_students_dept_id",
        "ix_students_batch",
        "ix_students_cgpa",
        "ix_students_status",
        "ix_students_verification_status",
        "ix_faculty_dept_id",
        "ix_placement_drives_company_id",
        "ix_placement_drives_batch",
        "ix_placement_drives_status",
        "ix_placement_drives_interview_date",
        "ix_placement_drives_deadline",
        "ix_applications_student_id",
        "ix_applications_drive_id",
        "ix_applications_status",
        "ix_interviews_student_id",
        "ix_interviews_application_id",
        "ix_interviews_status",
        "ix_feedbacks_interview_id",
        "ix_feedbacks_activity_id",
        "ix_notifications_user_id",
        "ix_notifications_is_read",
        "ix_system_logs_user_email",
        "ix_system_logs_action",
        "ix_parents_student_id",
        "ix_parents_mobile_number",
        "ix_parent_otps_mobile_number",
        "ix_permissions_user_id",
        "ix_permissions_module",
        "ix_permissions_status",
        "ix_access_requests_user_id",
        "ix_access_requests_status",
        "ix_correction_requests_student_id",
        "ix_correction_requests_status",
        "ix_placement_activities_company_id",
        "ix_placement_activities_placement_drive_id",
        "ix_placement_activities_date",
        "ix_activity_attendance_activity_id",
        "ix_activity_attendance_student_id",
        "ix_activity_attendance_status",
        "ix_grievances_student_id",
        "ix_grievances_status"
    ]
    
    missing = [idx for idx in expected_indexes if idx not in indexes]
    print(f"Total indexes in DB: {len(indexes)}")
    print(f"Missing indexes count: {len(missing)}")
    if missing:
        print("Missing indexes:", missing)
    assert len(missing) == 0, f"Found missing indexes: {missing}"
    print("PASS: All required foreign key and filter indexes exist in the database.")

def test_pagination_endpoints():
    print("\n--- Test 3: Pagination Endpoints ---")
    client = TestClient(app)
    db = SessionLocal()
    try:
        # Get admin user
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            # Create temporary admin token
            token = create_access_token(data={"sub": "admin@college.edu", "role": "admin"})
        else:
            token = create_access_token(data={"sub": admin.email, "role": admin.role})
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 3a: Notifications pagination (out of 33k rows)
        print("Testing /api/notifications default pagination...")
        resp = client.get("/api/notifications", headers=headers)
        assert resp.status_code == 200, f"Notifications returned {resp.status_code}: {resp.text}"
        notifs = resp.json()
        assert isinstance(notifs, list), "Expected list of notifications"
        assert len(notifs) <= 20, f"Expected default page size <= 20, got {len(notifs)}"
        print(f"PASS: /api/notifications returned {len(notifs)} items (default limit <= 20).")
        
        # Custom limit/offset on notifications
        resp_custom = client.get("/api/notifications?page=2&limit=5", headers=headers)
        assert resp_custom.status_code == 200
        assert len(resp_custom.json()) <= 5
        print("PASS: /api/notifications custom limit=5 works.")
        
        # Test 3b: Companies pagination
        print("Testing /api/companies pagination...")
        resp_all = client.get("/api/companies", headers=headers)
        assert resp_all.status_code == 200
        all_companies = resp_all.json()
        total_companies = len(all_companies)
        print(f"Total companies without limit: {total_companies}")
        
        resp_paginated = client.get("/api/companies?limit=2&page=1", headers=headers)
        assert resp_paginated.status_code == 200
        p_companies = resp_paginated.json()
        assert len(p_companies) <= 2
        print(f"PASS: /api/companies?limit=2 returned {len(p_companies)} companies.")
        
        # Test 3c: Students pagination (/api/students and /api/student/list)
        print("Testing /api/students pagination...")
        resp_st = client.get("/api/students?page=1&limit=5", headers=headers)
        assert resp_st.status_code == 200, f"Students failed: {resp_st.text}"
        data_st = resp_st.json()
        assert "total" in data_st
        assert "items" in data_st
        assert data_st["limit"] == 5
        assert len(data_st["items"]) <= 5
        print(f"PASS: /api/students returned {len(data_st['items'])} items (total={data_st['total']}).")
        
        # Test /api/student/list
        print("Testing /api/student/list alias endpoint...")
        resp_alias = client.get("/api/student/list?page=1&limit=5", headers=headers)
        assert resp_alias.status_code == 200, f"/api/student/list failed: {resp_alias.text}"
        data_alias = resp_alias.json()
        assert "total" in data_alias
        assert "items" in data_alias
        assert data_alias["limit"] == 5
        print(f"PASS: /api/student/list returned {len(data_alias['items'])} items.")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_alembic_revision()
    test_database_indexes()
    test_pagination_endpoints()
    print("\n==================================================")
    print("ALL PHASE 2 VERIFICATIONS PASSED SUCCESSFULLY!")
    print("==================================================")
