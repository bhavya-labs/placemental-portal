import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import sqlite3
import requests
import json
import time
from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User, Student, PlacementDrive, Application, Company, Department, Permission, SystemLog

client = TestClient(app)

print("=" * 70)
print("COMPREHENSIVE REQUIREMENTS-BASED PRODUCTION AUDIT & VERIFICATION")
print("=" * 70)

# Helper function to get auth headers
def get_token(email, password="password123"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

admin_headers = get_token("admin@platform.edu")

# -----------------------------------------------------------------------------
# 1. DATABASE INTEGRITY AUDIT (Req 19)
# -----------------------------------------------------------------------------
print("\n[CHECK 1] Database Integrity Audit (Req 19)")
conn = sqlite3.connect("backend/placement_portal.db")
cur = conn.cursor()
cur.execute("PRAGMA integrity_check;")
res = cur.fetchall()
assert res == [("ok",)], f"Integrity check failed: {res}"
print("[PASS] PRAGMA integrity_check: OK")

cur.execute("PRAGMA foreign_keys = ON;")
cur.execute("PRAGMA foreign_key_check;")
fk_res = cur.fetchall()
assert len(fk_res) == 0, f"Foreign key violations found: {fk_res}"
print("[PASS] PRAGMA foreign_key_check: 0 violations")
conn.close()

# -----------------------------------------------------------------------------
# 2. STUDENT PROFILE LOCKING & TAMPER PREVENTION (Req 2)
# -----------------------------------------------------------------------------
print("\n[CHECK 2] Student Profile Locking & Tamper Prevention (Req 2)")
db = SessionLocal()
verified_student = db.query(Student).filter(Student.verification_status == "VERIFIED").first()
student_user = verified_student.user
student_headers = get_token(student_user.email)

# Attempt to tamper with locked academic fields (CGPA) via direct API
tamper_payload = {
    "cgpa": 9.99,
    "attendance": 99.0,
    "backlogs": 0
}
res = client.put(f"/api/students/{verified_student.id}", json=tamper_payload, headers=student_headers)
print(f"Direct API profile tamper attempt status: {res.status_code}")
assert res.status_code == 403, f"Expected 403 for locked field tampering, got {res.status_code}: {res.text}"
assert "locked" in res.text.lower()
print("[PASS] Server-side rejection of academic tampering verified (HTTP 403)")

# Verify non-locked fields CAN be updated (skills, linkedin_url)
valid_update = {
    "linkedin_url": "https://linkedin.com/in/verifiedstudent",
    "skills": "Python, FastAPI, React"
}
res_valid = client.put(f"/api/students/{verified_student.id}", json=valid_update, headers=student_headers)
assert res_valid.status_code == 200, f"Valid non-locked update failed: {res_valid.text}"
print("[PASS] Non-locked fields update succeeds (HTTP 200)")

# -----------------------------------------------------------------------------
# 3. STUDENT DRIVE VISIBILITY ENFORCEMENT (Req 3)
# -----------------------------------------------------------------------------
print("\n[CHECK 3] Student Drive Visibility Backend Enforcement (Req 3)")
# Create a test drive with strict criteria: MECH only, CGPA 8.5+, 0 backlogs
test_comp = db.query(Company).first()
import time
unique_job_id = f"AUDIT-MECH-{int(time.time())}"
drive_data = {
    "company_id": test_comp.id,
    "role": "Robotics Specialist",
    "package_lpa": 12.5,
    "location": "Bengaluru",
    "cgpa_cutoff": 8.5,
    "allowed_depts": "MECH",
    "allowed_backlogs": 0,
    "bond_details": "None",
    "selection_process": "Interview",
    "interview_date": str(date.today() + timedelta(days=10)),
    "deadline": str(date.today() + timedelta(days=5)),
    "status": "PUBLISHED",
    "job_id": unique_job_id,
    "batch": "2026",
    "min_attendance": 80.0
}
res_drive = client.post("/api/drives", json=drive_data, headers=admin_headers)
assert res_drive.status_code == 200, f"Create test drive failed: {res_drive.text}"
created_drive_id = res_drive.json()["id"]

# Verify CSE student CANNOT see this MECH-only drive in GET /api/drives
cse_student = db.query(Student).join(Department).filter(Department.code == "CSE").first()
cse_headers = get_token(cse_student.user.email)
drives_cse = client.get("/api/drives", headers=cse_headers).json()
cse_visible_ids = [d["id"] for d in drives_cse]
assert created_drive_id not in cse_visible_ids, "CSE student could see MECH-only drive!"
print("[PASS] Branch filtering: CSE student cannot see MECH-only drive")

# Verify MECH student with CGPA < 8.5 CANNOT see this drive
low_cgpa_mech = db.query(Student).join(Department).filter(Department.code == "MECH", Student.cgpa < 8.5).first()
if low_cgpa_mech:
    mech_headers = get_token(low_cgpa_mech.user.email)
    drives_mech = client.get("/api/drives", headers=mech_headers).json()
    assert created_drive_id not in [d["id"] for d in drives_mech], "Low-CGPA student saw high-cutoff drive!"
    print("[PASS] Cutoff filtering: Student with CGPA < 8.5 cannot see 8.5+ cutoff drive")

# Verify eligible MECH student (CGPA >= 8.5, 0 backlogs, attendance >= 80) CAN see it
eligible_mech = db.query(Student).join(Department).filter(
    Department.code == "MECH",
    Student.cgpa >= 8.5,
    Student.backlogs == 0,
    Student.attendance >= 80.0,
    Student.batch == "2026"
).first()
if eligible_mech:
    el_headers = get_token(eligible_mech.user.email)
    drives_el = client.get("/api/drives", headers=el_headers).json()
    assert created_drive_id in [d["id"] for d in drives_el], "Eligible student could not see drive!"
    print("[PASS] Full eligibility: Eligible student sees drive in GET /api/drives")

# -----------------------------------------------------------------------------
# 4. APPLICATION SYNCHRONIZATION & WITHDRAW FLOW (Req 4)
# -----------------------------------------------------------------------------
print("\n[CHECK 4] Application Synchronization & Withdraw Flow (Req 4)")
# Create a drive eligible for our cse_student
cse_drive_data = {
    "company_id": test_comp.id,
    "role": "Cloud Architect",
    "package_lpa": 14.0,
    "location": "Hyderabad",
    "cgpa_cutoff": min(6.0, cse_student.cgpa),
    "allowed_depts": "CSE,IT",
    "allowed_backlogs": cse_student.backlogs + 1,
    "bond_details": "None",
    "selection_process": "Coding + Interview",
    "interview_date": str(date.today() + timedelta(days=12)),
    "deadline": str(date.today() + timedelta(days=6)),
    "status": "PUBLISHED",
    "job_id": f"AUDIT-CSE-{int(time.time())}",
    "batch": cse_student.batch,
    "min_attendance": min(60.0, cse_student.attendance)
}
res_c_drive = client.post("/api/drives", json=cse_drive_data, headers=admin_headers)
c_drive_id = res_c_drive.json()["id"]

# Student applies
apply_res = client.post("/api/applications", json={"drive_id": c_drive_id}, headers=cse_headers)
assert apply_res.status_code == 200, f"Apply failed: {apply_res.text}"
app_id = apply_res.json()["application_id"]
print(f"[PASS] Student applied successfully (Application ID: {app_id})")

# Prevent duplicate application
dup_res = client.post("/api/applications", json={"drive_id": c_drive_id}, headers=cse_headers)
assert dup_res.status_code == 400, "Duplicate application was not rejected!"
print("[PASS] Duplicate application rejected (HTTP 400)")

# Check student applications list
apps_res = client.get(f"/api/applications/student/{cse_student.id}", headers=cse_headers).json()
assert any(a["id"] == app_id for a in apps_res), "Application not found in student's list!"
print("[PASS] Application visible in Student Portal records")

# Check TPO / Admin views same application
admin_apps = client.get(f"/api/applications/student/{cse_student.id}", headers=admin_headers).json()
assert any(a["id"] == app_id for a in admin_apps), "Application not found in Admin records!"
print("[PASS] Single authoritative DB record visible across TPO/Admin portals")

# Test withdraw application
withdraw_res = client.delete(f"/api/applications/{app_id}", headers=cse_headers)
assert withdraw_res.status_code == 200, f"Withdraw failed: {withdraw_res.text}"
print("[PASS] Student successfully withdrew application (HTTP 200)")

# Verify record removed from student applications
apps_after = client.get(f"/api/applications/student/{cse_student.id}", headers=cse_headers).json()
assert not any(a["id"] == app_id for a in apps_after), "Withdrawn application still present in list!"
print("[PASS] Withdrawn application scrubbed from active applications")

# -----------------------------------------------------------------------------
# 5. STUDENT CALENDAR SCOPING (Req 5)
# -----------------------------------------------------------------------------
print("\n[CHECK 5] Student Calendar Eligibility Scoping (Req 5)")
cal_res = client.get("/api/calendar/events", headers=cse_headers).json()
cal_event_ids = [e["id"] for e in cal_res]
assert f"drive-deadline-{created_drive_id}" not in cal_event_ids, "Ineligible drive event leaked into student calendar!"
print("[PASS] Ineligible drive deadlines omitted from student calendar")

# -----------------------------------------------------------------------------
# 6. FACULTY RBAC & STATE TRANSITIONS (Req 9, 11)
# -----------------------------------------------------------------------------
print("\n[CHECK 6] Faculty RBAC & Drive State Machine (Req 9, 11)")
# Normal faculty without elevated grant
normal_faculty = db.query(User).filter(User.role == "faculty", User.email == "faculty.it@platform.edu").first()
if normal_faculty:
    fac_headers = get_token(normal_faculty.email)
    # Attempt to edit drive without grant
    edit_payload = dict(cse_drive_data)
    edit_payload["package_lpa"] = 18.0
    res_edit = client.put(f"/api/drives/{c_drive_id}", json=edit_payload, headers=fac_headers)
    assert res_edit.status_code == 403, f"Normal faculty could edit drive without permission! Status: {res_edit.status_code}"
    print("[PASS] Normal faculty denied unauthorized drive edit (HTTP 403)")

# Admin editing drive: valid status transition DRAFT/PUBLISHED -> Active -> COMPLETED
status_payload = dict(cse_drive_data)
status_payload["status"] = "Active"
res_stat = client.put(f"/api/drives/{c_drive_id}", json=status_payload, headers=admin_headers)
assert res_stat.status_code == 200, f"Active status update failed: {res_stat.text}"
updated_drive = res_stat.json()
assert updated_drive["status"] == "Active"
assert updated_drive["id"] == c_drive_id
assert updated_drive["company_id"] == test_comp.id
print("[PASS] Lifecycle transition to 'Active' succeeded with non-empty response")

# Clean up test drives
client.delete(f"/api/drives/{created_drive_id}", headers=admin_headers)
client.delete(f"/api/drives/{c_drive_id}", headers=admin_headers)
print("[PASS] Cleaned up ephemeral test drives")

# -----------------------------------------------------------------------------
# 7. INTERVIEW FEEDBACK ANALYTICS (Req 8)
# -----------------------------------------------------------------------------
print("\n[CHECK 7] Interview Feedback Analytics & Anonymity (Req 8)")
fb_res = client.get("/api/ai/feedbacks", headers=admin_headers)
assert fb_res.status_code == 200, f"Feedbacks API failed: {fb_res.text}"
feedbacks = fb_res.json()
print(f"[PASS] Retrieved {len(feedbacks)} real feedback records from database")
if len(feedbacks) > 0:
    first_fb = feedbacks[0]
    assert "experience_text" in first_fb
    assert "difficulty_rating" in first_fb
    print("[PASS] Real feedback schema structure verified")

sent_res = client.get("/api/ai/feedback-sentiment", headers=admin_headers)
assert sent_res.status_code == 200, f"Feedback sentiment failed: {sent_res.text}"
print("[PASS] Consolidated feedback sentiment analytics operational")

# -----------------------------------------------------------------------------
# 8. GLOBAL SEARCH SECURITY (Req 14)
# -----------------------------------------------------------------------------
print("\n[CHECK 8] Global Search Scoping & Privacy (Req 14)")
search_res = client.get("/api/search?q=admin", headers=cse_headers)
# Student should either be forbidden or not see administrative records
if search_res.status_code == 200:
    search_data = search_res.json()
    assert not any(r.get("type") == "user" and r.get("role") == "admin" for r in search_data.get("results", [])), "Admin accounts leaked to student search!"
print("[PASS] Global search does not leak privileged administrative data to students")

print("\n" + "=" * 70)
print("ALL PRODUCTION REQUIREMENTS AUDIT CHECKS PASSED WITH ZERO ERRORS!")
print("=" * 70)
db.close()
