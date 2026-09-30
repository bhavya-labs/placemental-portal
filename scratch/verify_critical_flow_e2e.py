import os
import sys
from datetime import datetime, timedelta, date

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal, Base, engine
from backend.app.models import User, Student, Parent, ParentOTP, Department, PlacementDrive, Application, Interview, Feedback, Company
from backend.app.auth import get_password_hash, create_access_token

client = TestClient(app)

def get_token(email: str, password: str = "password123") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    if res.status_code == 200:
        return res.json()["access_token"]
    raise Exception(f"Failed to login user {email}: {res.text}")

def run_critical_workflow_audit():
    print("--- STARTING E2E CRITICAL BUSINESS WORKFLOW AUDIT ---")
    db = SessionLocal()
    try:
        # Create a clean company for verification
        comp = db.query(Company).filter(Company.name == "Meta").first()
        if not comp:
            comp = Company(name="Meta", industry="Social Tech", website="meta.com", description="Metaverse")
            db.add(comp)
            db.commit()
            db.refresh(comp)

        # 1. Login/Authorize as TPO
        token_tnp = get_token("admin@platform.edu")
        headers_tnp = {"Authorization": f"Bearer {token_tnp}"}

        # 2-3. Create drive as DRAFT
        print("TPO creating drive as DRAFT...")
        res = client.post("/api/drives", json={
            "company_id": comp.id,
            "role": "Product Engineer",
            "package_lpa": 32.5,
            "location": "Hyderabad",
            "cgpa_cutoff": 8.0,
            "allowed_depts": "CSE",
            "allowed_backlogs": 0,
            "interview_date": (date.today() + timedelta(days=5)).isoformat(),
            "deadline": (date.today() + timedelta(days=3)).isoformat(),
            "status": "DRAFT",
            "batch": "2026",
            "min_attendance": 75.0
        }, headers=headers_tnp)
        assert res.status_code == 200, f"Failed to create drive: {res.text}"
        drive_id = res.json()["id"]
        print(f"Drive created successfully with ID: {drive_id}")

        # 4. Publish the drive
        print("TPO publishing the drive...")
        res = client.put(f"/api/drives/{drive_id}", json={
            "company_id": comp.id,
            "role": "Product Engineer",
            "package_lpa": 32.5,
            "location": "Hyderabad",
            "cgpa_cutoff": 8.0,
            "allowed_depts": "CSE",
            "allowed_backlogs": 0,
            "interview_date": (date.today() + timedelta(days=5)).isoformat(),
            "deadline": (date.today() + timedelta(days=3)).isoformat(),
            "status": "PUBLISHED",
            "batch": "2026",
            "min_attendance": 75.0
        }, headers=headers_tnp)
        assert res.status_code == 200, f"Failed to publish: {res.text}"

        # 5. Move drive to REGISTRATION_OPEN
        print("TPO shifting drive to REGISTRATION_OPEN...")
        res = client.put(f"/api/drives/{drive_id}", json={
            "company_id": comp.id,
            "role": "Product Engineer",
            "package_lpa": 32.5,
            "location": "Hyderabad",
            "cgpa_cutoff": 8.0,
            "allowed_depts": "CSE",
            "allowed_backlogs": 0,
            "interview_date": (date.today() + timedelta(days=5)).isoformat(),
            "deadline": (date.today() + timedelta(days=3)).isoformat(),
            "status": "REGISTRATION_OPEN",
            "batch": "2026",
            "min_attendance": 75.0
        }, headers=headers_tnp)
        assert res.status_code == 200, f"Failed to open registration: {res.text}"

        # 6-9. Login as eligible student (Student A: ID 16, CSE, Batch 2026, CGPA 8.6, Attendance 88.8, Backlogs 0)
        token_stud_a = get_token("student9@platform.edu")
        headers_stud_a = {"Authorization": f"Bearer {token_stud_a}"}

        print("Eligible Student A fetching drive details...")
        res = client.get(f"/api/drives/{drive_id}", headers=headers_stud_a)
        assert res.status_code == 200
        drive_details = res.json()
        assert drive_details["company_name"] == "Meta"
        assert drive_details["role"] == "Product Engineer"
        assert drive_details["package_lpa"] == 32.5
        assert drive_details["cgpa_cutoff"] == 8.0

        # 10. Verify eligibility for Student B (Radha Joshi: ID 9, ECE, CGPA 9.29, Attendance 81, Backlogs 0 - NOT ELIGIBLE due to branch CSE limit)
        token_stud_b = get_token("student2@platform.edu")
        headers_stud_b = {"Authorization": f"Bearer {token_stud_b}"}

        print("Testing eligibility enforcement: Student B (ECE) applying to CSE-only drive...")
        res = client.post("/api/applications", json={"drive_id": drive_id}, headers=headers_stud_b)
        print(f"Student B application response status: {res.status_code} (Expected: 400)")
        assert res.status_code == 400
        assert "not eligible" in res.json()["detail"].lower()

        # 11-12. Apply Student A (eligible)
        print("Eligible Student A applying to the drive...")
        res = client.post("/api/applications", json={"drive_id": drive_id}, headers=headers_stud_a)
        assert res.status_code == 200, f"Student A apply failed: {res.text}"
        app_id = res.json()["application_id"]
        print(f"Student A applied successfully. Application ID: {app_id}")

        # 13. Verify duplicate application is rejected
        print("Testing duplicate prevention: Student A applying again...")
        res = client.post("/api/applications", json={"drive_id": drive_id}, headers=headers_stud_a)
        assert res.status_code == 400
        assert "already applied" in res.json()["detail"].lower()

        # 14-16. Verify student's application appears in TPO applicant list
        # Let's search drive applications or get student applications
        print("TPO verification of applicants...")
        res = client.get(f"/api/applications/student/16", headers=headers_tnp)
        assert res.status_code == 200
        apps_list = res.json()
        matching_app = [a for a in apps_list if a["drive_id"] == drive_id]
        assert len(matching_app) == 1, "TPO could not retrieve Student A's application!"

        # 17-18. Change application status (Applied -> Shortlisted)
        print("TPO shortlisting Student A...")
        res = client.put(f"/api/applications/{app_id}/status", json={
            "status": "Shortlisted",
            "current_round": "Technical Round"
        }, headers=headers_tnp)
        assert res.status_code == 200

        print("Student A verifying updated application status...")
        res = client.get(f"/api/applications/student/16", headers=headers_stud_a)
        assert res.status_code == 200
        student_apps = res.json()
        matching_student_app = [a for a in student_apps if a["id"] == app_id][0]
        assert matching_student_app["status"] == "Shortlisted"

        # 19-20. Schedule interview and check notifications/calendar
        print("TPO scheduling interview round...")
        res = client.post("/api/interviews", json={
            "application_id": app_id,
            "round_name": "Technical Round 1",
            "interview_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "remarks": "Be prepared with System Design and DSA questions"
        }, headers=headers_tnp)
        assert res.status_code == 200
        interview_id = res.json()["interview_id"]

        print("Verifying interview event maps to student...")
        res = client.get("/api/calendar/events", headers=headers_stud_a)
        assert res.status_code == 200
        cal_events = res.json()
        assert len(cal_events) > 0, "No calendar events populated for student!"

        # 21-23. Submit interview feedback
        print("Student A submitting feedback on interview...")
        res = client.post(f"/api/interviews/{interview_id}/feedback", json={
            "interview_id": interview_id,
            "experience_text": "SQL database query round was very difficult. The SQL joins questions took most of the time.",
            "questions_asked": "Write a query to find the second highest salary, SQL joins vs subqueries.",
            "difficulty_rating": 4,
            "preparation_time": "2 days",
            "suggestions": "More practice on SQL queries"
        }, headers=headers_stud_a)
        assert res.status_code == 200, f"Failed to submit feedback: {res.text}"

        # 24-26. Submit another similar feedback to verify consolidation
        # Let's create another mock student interview feedback on SQL query round
        # First create another interview record
        # Note: Radha Joshi (ID 9) is CSE department? Wait, Radha Joshi (student2) is CSE or ECE?
        # Let's check her department. She is ECE. Let's register a mock interview for student 8's subsequent rounds to verify group consolidation!
        # First schedule another interview for Student A
        res = client.post("/api/interviews", json={
            "application_id": app_id,
            "round_name": "Technical Round 2",
            "interview_date": (datetime.now() + timedelta(days=3)).isoformat(),
            "remarks": "Final tech round"
        }, headers=headers_tnp)
        assert res.status_code == 200
        interview_id_2 = res.json()["interview_id"]

        print("Student A submitting second similar feedback on SQL query round...")
        res = client.post(f"/api/interviews/{interview_id_2}/feedback", json={
            "interview_id": interview_id_2,
            "experience_text": "DBMS query round was difficult. SQL database questions were confusing.",
            "questions_asked": "Write SQL queries to retrieve duplicate rows, index optimizations.",
            "difficulty_rating": 4,
            "preparation_time": "3 days",
            "suggestions": "Add SQL index query practice rounds"
        }, headers=headers_stud_a)
        assert res.status_code == 200

        # Now get drive feedback report and check theme consolidation
        print("TPO retrieving consolidated feedback report for Meta drive...")
        res = client.get(f"/api/feedback/report/drive/{drive_id}", headers=headers_tnp)
        assert res.status_code == 200, f"Get drive report failed: {res.text}"
        report = res.json()
        assert report["total_responses"] == 2
        themes = report["themes"]
        assert len(themes) > 0
        sql_theme = [t for t in themes if "SQL" in t["theme"] or "Database" in t["theme"]][0]
        # Check that both feedbacks were clustered into this theme!
        assert sql_theme["student_count"] == 2, "Feedbacks were not consolidated into a single theme!"
        print(f"Themes successfully consolidated! Merged Theme Name: {sql_theme['theme']}, Count: {sql_theme['student_count']}")

        # 27-28. TPO selects student
        print("TPO selecting Student A and accepting offer...")
        res = client.put(f"/api/applications/{app_id}/status", json={
            "status": "Selected",
            "current_round": "HR Round Completed",
            "joining_status": "Accepted",
            "remarks": "Outstanding candidate"
        }, headers=headers_tnp)
        assert res.status_code == 200

        print("Verifying student status changed to Placed...")
        res = client.get("/api/students/16", headers=headers_stud_a)
        assert res.status_code == 200
        student_data = res.json()
        assert student_data["status"] == "Placed"
        print("Student A status is Placed!")

        # Clean up created drive/applications to keep database clean
        db.query(Feedback).filter(Feedback.interview_id.in_([interview_id, interview_id_2])).delete()
        db.query(Interview).filter(Interview.id.in_([interview_id, interview_id_2])).delete()
        db.query(Application).filter(Application.id == app_id).delete()
        db.query(PlacementDrive).filter(PlacementDrive.id == drive_id).delete()
        db.commit()

        print("\nALL CRITICAL PLACEMENT E2E FLOW TEST STEPS PASSED!")
    finally:
        db.close()

if __name__ == '__main__':
    run_critical_workflow_audit()
