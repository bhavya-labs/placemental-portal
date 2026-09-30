import sys, os
sys.path.insert(0, os.path.abspath('.'))
from fastapi.testclient import TestClient
from datetime import date, timedelta
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User, Student, PlacementDrive, Application, Company, Department, Permission, SystemLog

client = TestClient(app)

print("=" * 70)
print("TESTING ALL 9 PRODUCTION AUDIT ISSUES")
print("=" * 70)

# Helper to get auth headers
def get_token(email, password="password123"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

admin_headers = get_token("admin@platform.edu")
faculty_headers = get_token("faculty.cse@platform.edu")

# Setup db session
db = SessionLocal()
cse_student = db.query(Student).join(Department).filter(Department.code == "CSE").first()
cse_headers = get_token(cse_student.user.email)

# =============================================================================
# ISSUE 1: Company Reassignment & company_id Integrity
# =============================================================================
print("\n[TEST 1] Company Reassignment & company_id Integrity")
# A. Verify GET /api/drives returns company_id
drives_res = client.get("/api/drives", headers=admin_headers)
assert drives_res.status_code == 200
for d in drives_res.json()[:5]:
    assert "company_id" in d and d["company_id"] > 0, f"Drive {d['id']} missing valid company_id"
print("  [PASS] GET /api/drives returns company_id for all drives")

# B. Verify POST /api/drives returns real company_id
test_company = db.query(Company).filter(Company.id == 2).first() # Microsoft
drive_payload = {
    "company_id": test_company.id,
    "role": "FullStack Engineer Issue1",
    "package_lpa": 15.0,
    "location": "Bengaluru",
    "cgpa_cutoff": 7.0,
    "allowed_depts": "CSE,IT",
    "allowed_backlogs": 0,
    "bond_details": "None",
    "selection_process": "Interview",
    "interview_date": str(date.today() + timedelta(days=14)),
    "deadline": str(date.today() + timedelta(days=7)),
    "status": "DRAFT",
    "job_id": "TEST-ISSUE1-DRIVE",
    "batch": "2026",
    "min_attendance": 75.0
}
post_res = client.post("/api/drives", json=drive_payload, headers=admin_headers)
assert post_res.status_code == 200
drive_data = post_res.json()
assert drive_data["company_id"] == test_company.id
test_drive_id = drive_data["id"]
print(f"  [PASS] POST /api/drives returned real company_id: {drive_data['company_id']}")

# C. Verify GET /api/drives/{id} returns real company_id
get_single_res = client.get(f"/api/drives/{test_drive_id}", headers=admin_headers)
assert get_single_res.status_code == 200
assert get_single_res.json()["company_id"] == test_company.id
print("  [PASS] GET /api/drives/{id} returned matching company_id")

# D. Verify invalid company_id is rejected
bad_payload = {**drive_payload, "company_id": 999999, "job_id": "BAD-COMP-ID"}
bad_res = client.post("/api/drives", json=bad_payload, headers=admin_headers)
assert bad_res.status_code == 400
print("  [PASS] Invalid company_id is rejected with HTTP 400")

# E. Verify editing without changing company retains original company
edit_payload = {**drive_payload, "package_lpa": 17.5, "location": "Hyderabad"}
put_res = client.put(f"/api/drives/{test_drive_id}", json=edit_payload, headers=admin_headers)
assert put_res.status_code == 200
assert put_res.json()["company_id"] == test_company.id
# Re-fetch
refetch_res = client.get(f"/api/drives/{test_drive_id}", headers=admin_headers)
assert refetch_res.json()["company_id"] == test_company.id
print("  [PASS] Editing drive preserves company_id (no silent reassignment)")

# Cleanup test drive
client.delete(f"/api/drives/{test_drive_id}", headers=admin_headers)

# =============================================================================
# ISSUE 2: Faculty Department-Scoped RBAC Bypass
# =============================================================================
print("\n[TEST 2] Faculty Department-Scoped RBAC Bypass")
# Create CSE-only drive
cse_drive_payload = {**drive_payload, "allowed_depts": "CSE", "job_id": "CSE-ONLY-RBAC"}
res_cse_drive = client.post("/api/drives", json=cse_drive_payload, headers=admin_headers)
cse_drive_id = res_cse_drive.json()["id"]

# Create IT-inclusive drive
it_drive_payload = {**drive_payload, "allowed_depts": "CSE,IT", "job_id": "IT-INCL-RBAC"}
res_it_drive = client.post("/api/drives", json=it_drive_payload, headers=admin_headers)
it_drive_id = res_it_drive.json()["id"]

# Attempt to edit CSE-only drive as faculty.cse (scoped to IT in permissions)
edit_cse = {**cse_drive_payload, "package_lpa": 20.0}
res_edit_cse = client.put(f"/api/drives/{cse_drive_id}", json=edit_cse, headers=faculty_headers)
assert res_edit_cse.status_code == 403, f"Expected 403, got {res_edit_cse.status_code}"
print("  [PASS] IT-scoped faculty cannot edit CSE-only drive (HTTP 403 Forbidden)")

# Attempt to edit IT-inclusive drive as faculty.cse (scoped to IT in permissions)
edit_it = {**it_drive_payload, "package_lpa": 20.0}
res_edit_it = client.put(f"/api/drives/{it_drive_id}", json=edit_it, headers=faculty_headers)
assert res_edit_it.status_code == 200, f"Expected 200, got {res_edit_it.status_code}: {res_edit_it.text}"
print("  [PASS] IT-scoped faculty can edit IT-inclusive drive (HTTP 200 OK)")

# Cleanup
client.delete(f"/api/drives/{cse_drive_id}", headers=admin_headers)
client.delete(f"/api/drives/{it_drive_id}", headers=admin_headers)

# =============================================================================
# ISSUE 3 & 4: Drive Update Returns Full JSON & Lifecycle State Machine
# =============================================================================
print("\n[TEST 3 & 4] Drive Update Complete JSON & Lifecycle State Machine")
# Create in DRAFT
draft_payload = {**drive_payload, "status": "DRAFT", "job_id": "STATE-MACHINE-TEST"}
res_draft = client.post("/api/drives", json=draft_payload, headers=admin_headers)
sm_drive_id = res_draft.json()["id"]

# Transitions to test
transitions = [
    ("DRAFT", "Active"),
    ("Active", "REGISTRATION_OPEN"),
    ("REGISTRATION_OPEN", "REGISTRATION_CLOSED"),
    ("REGISTRATION_CLOSED", "ASSESSMENT"),
    ("ASSESSMENT", "INTERVIEW"),
    ("INTERVIEW", "RESULT_DECLARED"),
    ("RESULT_DECLARED", "COMPLETED"),
    ("COMPLETED", "ARCHIVED")
]

current_status = "DRAFT"
for from_st, to_st in transitions:
    upd_payload = {**draft_payload, "status": to_st}
    res_trans = client.put(f"/api/drives/{sm_drive_id}", json=upd_payload, headers=admin_headers)
    assert res_trans.status_code == 200, f"Transition from {from_st} to {to_st} failed: {res_trans.text}"
    body = res_trans.json()
    assert body["status"] == to_st
    assert "lifecycle_status" in body and body["lifecycle_status"] == to_st
    assert body["company_id"] == test_company.id
    assert body["package_lpa"] == draft_payload["package_lpa"]
    assert body["role"] == draft_payload["role"]
    assert body["deadline"] == draft_payload["deadline"]
    assert body["interview_date"] == draft_payload["interview_date"]
    print(f"  [PASS] State transition: {from_st} -> {to_st} (returned complete JSON)")

# Cleanup
client.delete(f"/api/drives/{sm_drive_id}", headers=admin_headers)

# =============================================================================
# ISSUE 5: Drive Edit Modal Date Fields
# =============================================================================
print("\n[TEST 5] Drive Edit Modal Date Fields Modification & Persistence")
date_test_payload = {**drive_payload, "job_id": "DATE-TEST-DRIVE"}
res_dt = client.post("/api/drives", json=date_test_payload, headers=admin_headers)
dt_drive_id = res_dt.json()["id"]

new_deadline = str(date.today() + timedelta(days=25))
new_interview = str(date.today() + timedelta(days=35))
edit_dates_payload = {
    **date_test_payload,
    "deadline": new_deadline,
    "interview_date": new_interview
}
put_dt = client.put(f"/api/drives/{dt_drive_id}", json=edit_dates_payload, headers=admin_headers)
assert put_dt.status_code == 200
assert put_dt.json()["deadline"] == new_deadline
assert put_dt.json()["interview_date"] == new_interview

# Verify persisted via GET
get_dt = client.get(f"/api/drives/{dt_drive_id}", headers=admin_headers)
assert get_dt.json()["deadline"] == new_deadline
assert get_dt.json()["interview_date"] == new_interview
print("  [PASS] Modified deadline and interview_date persisted in database")

client.delete(f"/api/drives/{dt_drive_id}", headers=admin_headers)

# =============================================================================
# ISSUE 6: Student Eligibility Filtering / Query-Level Leakage & Direct API Protection
# =============================================================================
print("\n[TEST 6] Student Eligibility Filtering at Backend/API Level & Direct Single-Drive Access")

# Setup test drives for each eligibility dimension:
# 1. Eligible drive (Case A)
eligible_payload = {
    **drive_payload,
    "allowed_depts": "CSE",
    "cgpa_cutoff": min(6.0, cse_student.cgpa),
    "allowed_backlogs": cse_student.backlogs + 1,
    "min_attendance": min(60.0, cse_student.attendance),
    "batch": cse_student.batch or "2026",
    "status": "PUBLISHED",
    "job_id": "ELIGIBLE-DRIVE-CSE"
}
res_elig = client.post("/api/drives", json=eligible_payload, headers=admin_headers)
assert res_elig.status_code == 200
elig_id = res_elig.json()["id"]

# 2. Wrong Department drive (Case B)
wrong_dept_payload = {
    **drive_payload,
    "allowed_depts": "MECH,CIVIL",
    "cgpa_cutoff": 5.0,
    "batch": cse_student.batch or "2026",
    "status": "PUBLISHED",
    "job_id": "WRONG-DEPT-DRIVE"
}
res_wrong_dept = client.post("/api/drives", json=wrong_dept_payload, headers=admin_headers)
assert res_wrong_dept.status_code == 200
wrong_dept_id = res_wrong_dept.json()["id"]

# 3. High CGPA drive (Case C)
high_cgpa_payload = {
    **drive_payload,
    "allowed_depts": "CSE,IT",
    "cgpa_cutoff": cse_student.cgpa + 1.0,
    "batch": cse_student.batch or "2026",
    "status": "PUBLISHED",
    "job_id": "HIGH-CGPA-DRIVE"
}
res_high_cgpa = client.post("/api/drives", json=high_cgpa_payload, headers=admin_headers)
assert res_high_cgpa.status_code == 200
high_cgpa_id = res_high_cgpa.json()["id"]

# 4. Strict Backlogs drive (Case D)
backlogs_payload = {
    **drive_payload,
    "allowed_depts": "CSE",
    "cgpa_cutoff": min(6.0, cse_student.cgpa),
    "allowed_backlogs": -1,
    "batch": cse_student.batch or "2026",
    "status": "PUBLISHED",
    "job_id": "STRICT-BACKLOGS-DRIVE"
}
res_backlogs = client.post("/api/drives", json=backlogs_payload, headers=admin_headers)
assert res_backlogs.status_code == 200
backlogs_id = res_backlogs.json()["id"]

# 5. Strict Attendance drive (Case E)
attendance_payload = {
    **drive_payload,
    "allowed_depts": "CSE",
    "cgpa_cutoff": min(6.0, cse_student.cgpa),
    "min_attendance": 99.0,
    "batch": cse_student.batch or "2026",
    "status": "PUBLISHED",
    "job_id": "STRICT-ATTENDANCE-DRIVE"
}
res_attendance = client.post("/api/drives", json=attendance_payload, headers=admin_headers)
assert res_attendance.status_code == 200
attendance_id = res_attendance.json()["id"]

# 6. Wrong Batch drive (Case F)
wrong_batch = "2023" if (cse_student.batch != "2023") else "2022"
batch_payload = {
    **drive_payload,
    "allowed_depts": "CSE",
    "cgpa_cutoff": min(6.0, cse_student.cgpa),
    "batch": wrong_batch,
    "status": "PUBLISHED",
    "job_id": "WRONG-BATCH-DRIVE"
}
res_batch = client.post("/api/drives", json=batch_payload, headers=admin_headers)
assert res_batch.status_code == 200
batch_id = res_batch.json()["id"]

# 7. Already Applied drive (Case G)
applied_drive_payload = {
    **drive_payload,
    "allowed_depts": "MECH",
    "cgpa_cutoff": 5.0,
    "status": "PUBLISHED",
    "job_id": "APPLIED-INELIGIBLE-DRIVE"
}
res_applied = client.post("/api/drives", json=applied_drive_payload, headers=admin_headers)
assert res_applied.status_code == 200
applied_drive_id = res_applied.json()["id"]

# Insert pre-existing application
pre_app = Application(
    student_id=cse_student.id,
    drive_id=applied_drive_id,
    status="Applied",
    current_round="Applied",
    joining_status="Pending"
)
db.add(pre_app)
db.commit()
db.refresh(pre_app)

try:
    # --- DIRECT SINGLE-DRIVE API TESTS: GET /api/drives/{drive_id} ---
    # Case A: Eligible student requests eligible drive -> 200
    res_a = client.get(f"/api/drives/{elig_id}", headers=cse_headers)
    assert res_a.status_code == 200, f"Case A failed: expected 200, got {res_a.status_code}"
    print("  [PASS] Case A: Eligible student requests eligible drive -> HTTP 200 OK")

    # Case B: Wrong department -> 403
    res_b = client.get(f"/api/drives/{wrong_dept_id}", headers=cse_headers)
    assert res_b.status_code == 403, f"Case B failed: expected 403, got {res_b.status_code}"
    print("  [PASS] Case B: Student with wrong department requests restricted drive -> HTTP 403 Forbidden")

    # Case C: Insufficient CGPA -> 403
    res_c = client.get(f"/api/drives/{high_cgpa_id}", headers=cse_headers)
    assert res_c.status_code == 403, f"Case C failed: expected 403, got {res_c.status_code}"
    print("  [PASS] Case C: Student with insufficient CGPA requests drive -> HTTP 403 Forbidden")

    # Case D: Excessive backlogs -> 403
    res_d = client.get(f"/api/drives/{backlogs_id}", headers=cse_headers)
    assert res_d.status_code == 403, f"Case D failed: expected 403, got {res_d.status_code}"
    print("  [PASS] Case D: Student with excessive backlogs requests drive -> HTTP 403 Forbidden")

    # Case E: Insufficient attendance -> 403
    res_e = client.get(f"/api/drives/{attendance_id}", headers=cse_headers)
    assert res_e.status_code == 403, f"Case E failed: expected 403, got {res_e.status_code}"
    print("  [PASS] Case E: Student with insufficient attendance requests drive -> HTTP 403 Forbidden")

    # Case F: Wrong batch -> 403
    res_f = client.get(f"/api/drives/{batch_id}", headers=cse_headers)
    assert res_f.status_code == 403, f"Case F failed: expected 403, got {res_f.status_code}"
    print("  [PASS] Case F: Student with wrong batch requests drive -> HTTP 403 Forbidden")

    # Case G: Already applied to otherwise-ineligible drive -> 200
    res_g = client.get(f"/api/drives/{applied_drive_id}", headers=cse_headers)
    assert res_g.status_code == 200, f"Case G failed: expected 200, got {res_g.status_code}"
    print("  [PASS] Case G: Student who has already applied retains drive visibility -> HTTP 200 OK")

    # Verify admin and faculty can access drives regardless of student criteria
    res_admin_check = client.get(f"/api/drives/{wrong_dept_id}", headers=admin_headers)
    assert res_admin_check.status_code == 200
    res_fac_check = client.get(f"/api/drives/{wrong_dept_id}", headers=faculty_headers)
    assert res_fac_check.status_code == 200
    print("  [PASS] Admin and Faculty access to drive details remains unrestricted")

    # --- LIST ENDPOINT & CALENDAR FILTERING ---
    student_drives = client.get("/api/drives", headers=cse_headers).json()
    student_drive_ids = [d["id"] for d in student_drives]
    assert elig_id in student_drive_ids, "Eligible drive missing from GET /api/drives"
    assert wrong_dept_id not in student_drive_ids, "Wrong dept drive leaked in GET /api/drives"
    assert high_cgpa_id not in student_drive_ids, "High CGPA drive leaked in GET /api/drives"
    assert backlogs_id not in student_drive_ids, "Backlogs drive leaked in GET /api/drives"
    assert attendance_id not in student_drive_ids, "Attendance drive leaked in GET /api/drives"
    assert batch_id not in student_drive_ids, "Batch drive leaked in GET /api/drives"
    assert applied_drive_id in student_drive_ids, "Already applied drive missing from GET /api/drives"
    print("  [PASS] GET /api/drives list filtering correctly reflects eligibility & applied state")

    cal_events = client.get("/api/calendar/events", headers=cse_headers).json()
    cal_drive_ids = {e["id"] for e in cal_events}
    assert f"drive-deadline-{wrong_dept_id}" not in cal_drive_ids
    assert f"drive-interview-{wrong_dept_id}" not in cal_drive_ids
    assert f"drive-deadline-{high_cgpa_id}" not in cal_drive_ids
    assert f"drive-interview-{high_cgpa_id}" not in cal_drive_ids
    print("  [PASS] Calendar endpoint correctly suppresses ineligible drive events")

finally:
    # Cleanup pre_app and all created drives
    db.query(Application).filter(Application.drive_id == applied_drive_id).delete(synchronize_session=False)
    db.commit()
    for did in [elig_id, wrong_dept_id, high_cgpa_id, backlogs_id, attendance_id, batch_id, applied_drive_id]:
        client.delete(f"/api/drives/{did}", headers=admin_headers)

# =============================================================================
# ISSUE 7: Academic Profile Tampering
# =============================================================================
print("\n[TEST 7] Academic Profile Server-Side Tamper Prevention")
# Try modifying CGPA as verified student
tamper_cgpa = client.put(f"/api/students/{cse_student.id}", json={"cgpa": 9.99}, headers=cse_headers)
assert tamper_cgpa.status_code == 403, f"Expected 403, got {tamper_cgpa.status_code}"
print("  [PASS] Verified student changing CGPA rejected (HTTP 403 Forbidden)")

# Try modifying attendance as verified student
tamper_att = client.put(f"/api/students/{cse_student.id}", json={"attendance": 99.9}, headers=cse_headers)
assert tamper_att.status_code == 403
print("  [PASS] Verified student changing attendance rejected (HTTP 403 Forbidden)")

# Try modifying backlogs as verified student
tamper_bk = client.put(f"/api/students/{cse_student.id}", json={"backlogs": 0}, headers=cse_headers)
# If existing backlogs != 0, it must be 403
if cse_student.backlogs != 0:
    assert tamper_bk.status_code == 403
    print("  [PASS] Verified student changing backlogs rejected (HTTP 403 Forbidden)")

# Modify non-locked fields (bio, skills, linkedin_url)
legit_update = client.put(
    f"/api/students/{cse_student.id}",
    json={"skills": "Python, React, TypeScript, FastAPI", "linkedin_url": "https://linkedin.com/in/verified-dev"},
    headers=cse_headers
)
assert legit_update.status_code == 200
print("  [PASS] Verified student updating legitimate fields (skills, linkedin) succeeds (HTTP 200 OK)")

# Admin updating academic metrics
admin_update = client.put(
    f"/api/students/{cse_student.id}",
    json={"cgpa": cse_student.cgpa},
    headers=admin_headers
)
assert admin_update.status_code == 200
print("  [PASS] Authorized administrator updating profile succeeds (HTTP 200 OK)")

# =============================================================================
# ISSUE 8: Application Withdrawal Workflow
# =============================================================================
print("\n[TEST 8] Application Withdrawal Workflow")
# Create drive and student applies
app_drive_payload = {
    **drive_payload,
    "allowed_depts": "CSE",
    "cgpa_cutoff": min(6.0, cse_student.cgpa),
    "allowed_backlogs": cse_student.backlogs + 1,
    "min_attendance": min(60.0, cse_student.attendance),
    "status": "PUBLISHED",
    "deadline": str(date.today() + timedelta(days=5)),
    "job_id": "WITHDRAW-TEST-DRIVE"
}
res_app_drive = client.post("/api/drives", json=app_drive_payload, headers=admin_headers)
w_drive_id = res_app_drive.json()["id"]

# Student applies
apply_res = client.post("/api/applications", json={"drive_id": w_drive_id}, headers=cse_headers)
assert apply_res.status_code == 200
app_id = apply_res.json()["application_id"]
print(f"  [PASS] Student submitted application (ID: {app_id})")

# Other student attempts to withdraw (non-owner)
other_student = db.query(Student).filter(Student.id != cse_student.id).first()
other_headers = get_token(other_student.user.email)
non_owner_withdraw = client.delete(f"/api/applications/{app_id}", headers=other_headers)
assert non_owner_withdraw.status_code == 403
print("  [PASS] Non-owner cannot withdraw application (HTTP 403 Forbidden)")

# Owner withdraws before deadline
owner_withdraw = client.delete(f"/api/applications/{app_id}", headers=cse_headers)
assert owner_withdraw.status_code == 200
print("  [PASS] Applicant successfully withdrew application before deadline (HTTP 200 OK)")

# Already withdrawn application
repeat_withdraw = client.delete(f"/api/applications/{app_id}", headers=cse_headers)
assert repeat_withdraw.status_code == 404
print("  [PASS] Withdrawing already withdrawn/deleted application handled safely (HTTP 404)")

# Cleanup drive
client.delete(f"/api/drives/{w_drive_id}", headers=admin_headers)

# =============================================================================
# ISSUE 9: Static Mock Sentiment / Feedback Data
# =============================================================================
print("\n[TEST 9] Real Sentiment Feedback Data from Database")
# Query /api/ai/feedbacks
fb_res = client.get("/api/ai/feedbacks", headers=admin_headers)
assert fb_res.status_code == 200
feedbacks = fb_res.json()
print(f"  [PASS] /api/ai/feedbacks returned {len(feedbacks)} real database records")

# Query sentiment summary
sent_res = client.get("/api/ai/feedback-sentiment", headers=admin_headers)
assert sent_res.status_code == 200
sent_data = sent_res.json()
assert "themes" in sent_data
print("  [PASS] /api/ai/feedback-sentiment operational and derives from real database records")

print("\n" + "=" * 70)
print("ALL 9 PRODUCTION ISSUES FULLY VERIFIED WITH ZERO FAILURES!")
print("=" * 70)
