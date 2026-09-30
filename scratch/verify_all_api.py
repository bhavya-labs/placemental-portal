import os
import sys
from fastapi.testclient import TestClient

# Insert project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Student, Parent, ParentOTP, User, CorrectionRequest

client = TestClient(app)

def test_parent_flow():
    print("--- Testing Parent Portal OTP & Authentication Flow ---")
    db = SessionLocal()
    try:
        # Get a student roll number
        student = db.query(Student).first()
        if not student:
            print("ERROR: No student found to test parent flow!")
            return
        
        roll_number = student.id
        mobile = "9988776655"
        
        # Insert parent record if not exists
        parent = db.query(Parent).filter(Parent.student_id == roll_number).first()
        if not parent:
            parent = Parent(student_id=roll_number, parent_name="Test Parent", mobile_number=mobile, relationship="Father")
            db.add(parent)
            db.commit()
        else:
            mobile = parent.mobile_number

        # 1. Request OTP
        print(f"Requesting OTP for Roll: {roll_number}, Mobile: {mobile}...")
        resp = client.post("/api/parent/request-otp", json={
            "roll_number": roll_number,
            "mobile_number": mobile
        })
        assert resp.status_code == 200, f"Request OTP failed: {resp.text}"
        otp_data = resp.json()
        otp_code = otp_data.get("otp_debug")
        print(f"OTP received from simulator: {otp_code}")

        # 2. Verify OTP
        print("Verifying OTP...")
        resp_verify = client.post("/api/parent/verify-otp", json={
            "roll_number": roll_number,
            "mobile_number": mobile,
            "otp": otp_code
        })
        assert resp_verify.status_code == 200, f"Verify OTP failed: {resp_verify.text}"
        token_data = resp_verify.json()
        token = token_data.get("access_token")
        print("Parent authentication token generated successfully!")

        # 3. Retrieve Child Dashboard
        print("Fetching Child details using Parent session...")
        headers = {"Authorization": f"Bearer {token}"}
        resp_child = client.get("/api/parent/child", headers=headers)
        assert resp_child.status_code == 200, f"Child dashboard retrieval failed: {resp_child.text}"
        child_data = resp_child.json()
        print(f"Child profile loaded successfully! Name: {child_data['student']['name']}, CGPA: {child_data['student']['cgpa']}")

    finally:
        db.close()

def test_profile_locking_and_correction():
    print("\n--- Testing Student Profile Locks & Admin Correction Request Workflow ---")
    db = SessionLocal()
    try:
        # Get first student
        student = db.query(Student).filter(Student.verification_status == 'VERIFIED').first()
        if not student:
            print("ERROR: No verified student found!")
            return
            
        student_email = student.user.email
        student_id = student.id
        print(f"Targeting Verified Student: {student.user.name} (ID: {student_id}, Email: {student_email})")

        # Login as student to get token
        resp_login = client.post("/api/auth/login", json={
            "email": student_email,
            "password": "password123"
        })
        assert resp_login.status_code == 200, "Student login failed"
        student_token = resp_login.json()["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}

        # 1. Attempt to directly update locked field (CGPA)
        print("Attempting to modify locked CGPA field directly...")
        resp_update = client.put(f"/api/students/{student_id}", json={
            "cgpa": 9.99
        }, headers=student_headers)
        
        # Should return 403 Forbidden
        print(f"Direct update response status: {resp_update.status_code} (Expected: 403)")
        assert resp_update.status_code == 403, f"Locked field was directly updated: {resp_update.text}"
        print("SUCCESS: Student profile locks verified successfully!")

        # 2. File Correction Request
        print("Filing correction request for CGPA: 9.29 -> 9.41...")
        resp_correct = client.post("/api/students/correction-requests", json={
            "field": "CGPA",
            "current_value": "9.29",
            "requested_value": "9.41",
            "reason": "Re-valuation sem result correction"
        }, headers=student_headers)
        assert resp_correct.status_code == 200, f"Submit correction request failed: {resp_correct.text}"
        req_id = resp_correct.json()["id"]
        print(f"Correction request submitted successfully! Request ID: {req_id}")

        # 3. Process Request as Admin
        # Login as admin
        resp_admin_login = client.post("/api/auth/login", json={
            "email": "admin@platform.edu",
            "password": "password123"
        })
        assert resp_admin_login.status_code == 200, "Admin login failed"
        admin_token = resp_admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        print("Approving correction request as Admin...")
        resp_approve = client.put(f"/api/students/correction-requests/{req_id}/action", json={
            "status": "Approved"
        }, headers=admin_headers)
        assert resp_approve.status_code == 200, f"Action failed: {resp_approve.text}"
        
        # Verify db updated
        db.expire(student)
        db.refresh(student)
        print(f"Verified Student CGPA updated in database! Current CGPA: {student.cgpa} (Expected: 9.41)")
        assert student.cgpa == 9.41, "Student database CGPA did not update!"
        print("SUCCESS: Admin correction approval workflow verified!")

    finally:
        db.close()

if __name__ == '__main__':
    test_parent_flow()
    test_profile_locking_and_correction()
    print("\nAll integration API tests passed successfully!")
