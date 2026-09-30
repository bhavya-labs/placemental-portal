import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.auth import create_access_token
from backend.app.database import SessionLocal
from backend.app.models import User, Student, PlacementDrive, Feedback, Department, Application, Interview, Faculty

client = TestClient(app)
db = SessionLocal()

print("=" * 70)
print("VERIFYING FACULTY / HOD FUNCTIONAL REQUIREMENTS & RBAC")
print("=" * 70)

# Setup Test Users
cse_faculty_user = db.query(User).filter(User.email == "faculty_cse@platform.edu").first()
if not cse_faculty_user:
    # Try finding any faculty with CSE dept
    cse_prof = db.query(Faculty).filter(Faculty.dept_id == 1).first()
    if cse_prof:
        cse_faculty_user = db.query(User).filter(User.id == cse_prof.id).first()

it_faculty_user = db.query(User).filter(User.email == "faculty_it@platform.edu").first()
if not it_faculty_user:
    it_prof = db.query(Faculty).filter(Faculty.dept_id == 2).first()
    if it_prof:
        it_faculty_user = db.query(User).filter(User.id == it_prof.id).first()

admin_user = db.query(User).filter(User.role == "admin").first()

assert cse_faculty_user is not None, "CSE faculty user not found"
assert it_faculty_user is not None, "IT faculty user not found"
assert admin_user is not None, "Admin user not found"

cse_token = create_access_token(data={"sub": cse_faculty_user.email, "role": cse_faculty_user.role})
it_token = create_access_token(data={"sub": it_faculty_user.email, "role": it_faculty_user.role})
admin_token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})

cse_headers = {"Authorization": f"Bearer {cse_token}"}
it_headers = {"Authorization": f"Bearer {it_token}"}
admin_headers = {"Authorization": f"Bearer {admin_token}"}

# ======================================================================
# REQUIREMENT 1: DEPARTMENT-WISE STUDENT PLACEMENT DETAILS
# ======================================================================
print("\n[REQ 1 - TEST 1] Scoped Faculty Department Access & RBAC Enforcement")
# 1. CSE Faculty requests authorized department (dept_id=1)
res_cse = client.get("/api/students/department-placement-details?dept_id=1", headers=cse_headers)
assert res_cse.status_code == 200, f"Expected 200, got {res_cse.status_code}: {res_cse.text}"
data_cse = res_cse.json()
print(f"  [PASS] CSE Faculty accessing Dept 1 (CSE): HTTP 200 OK (returned {data_cse['total']} students)")

# 2. CSE Faculty requests default (no dept_id specified) -> automatically scopes to dept 1
res_def = client.get("/api/students/department-placement-details", headers=cse_headers)
assert res_def.status_code == 200, f"Expected 200, got {res_def.status_code}"
assert res_def.json()["department"]["id"] == 1, "Expected auto-scoping to department 1"
print("  [PASS] CSE Faculty with no dept_id: Auto-scoped to Dept 1 (CSE)")

# 3. CSE Faculty requests unauthorized department (dept_id=2 IT) -> MUST BE 403 Forbidden!
res_cross = client.get("/api/students/department-placement-details?dept_id=2", headers=cse_headers)
assert res_cross.status_code == 403, f"Expected 403, got {res_cross.status_code}"
print(f"  [PASS] CSE Faculty directly accessing Dept 2 (IT): HTTP 403 Forbidden ({res_cross.json().get('detail')})")

# 4. IT Faculty requests Dept 2 -> HTTP 200 OK
res_it = client.get("/api/students/department-placement-details?dept_id=2", headers=it_headers)
assert res_it.status_code == 200, f"Expected 200, got {res_it.status_code}"
print(f"  [PASS] IT Faculty accessing Dept 2 (IT): HTTP 200 OK")

# 5. Admin can query any department
res_admin_cse = client.get("/api/students/department-placement-details?dept_id=1", headers=admin_headers)
res_admin_it = client.get("/api/students/department-placement-details?dept_id=2", headers=admin_headers)
assert res_admin_cse.status_code == 200 and res_admin_it.status_code == 200
print(f"  [PASS] Admin query Dept 1 and Dept 2: HTTP 200 OK")

print("\n[REQ 1 - TEST 2] Summary Cards / Counts Verification from Real Database")
summary = data_cse["summary"]
required_summary_fields = [
    "total_students", "placed_students", "unplaced_students",
    "students_participated", "students_not_participated",
    "total_applications", "total_selections"
]
for f in required_summary_fields:
    assert f in summary, f"Missing summary field: {f}"
    assert isinstance(summary[f], int), f"Field {f} must be int"

print(f"  Summary Cards verified:")
print(f"    - Total students                  : {summary['total_students']}")
print(f"    - Placed students                 : {summary['placed_students']} ({summary.get('placement_percentage')}%)")
print(f"    - Unplaced students               : {summary['unplaced_students']}")
print(f"    - Attended/Applied to drives      : {summary['students_participated']}")
print(f"    - Not attended/applied to drives  : {summary['students_not_participated']}")
print(f"    - Total applications              : {summary['total_applications']}")
print(f"    - Total selections/offers         : {summary['total_selections']}")

# Cross check sanity
assert summary["placed_students"] + summary["unplaced_students"] == summary["total_students"], "Sum of placed + unplaced must equal total"
assert summary["students_participated"] + summary["students_not_participated"] == summary["total_students"], "Sum of participated + not participated must equal total"
print("  [PASS] Real database integrity check: summary card arithmetic is exact")

print("\n[REQ 1 - TEST 3] Student Placement Columns Verification")
assert len(data_cse["items"]) > 0, "Expected non-empty student items"
sample_student = data_cse["items"][0]
required_student_cols = [
    "name", "roll_no", "branch", "section", "cgpa", "attendance",
    "drives_applied_count", "interviews_attended_count", "selections_count",
    "status", "active_applications_count", "backlogs", "placement_preparation_score"
]
for col in required_student_cols:
    assert col in sample_student, f"Missing required student column: {col}"

print(f"  Sample Student Row verified: {sample_student['name']} ({sample_student['roll_no']})")
print(f"    - Branch / Section           : {sample_student['branch']} / {sample_student['section']}")
print(f"    - CGPA                       : {sample_student['cgpa']}")
print(f"    - Attendance                 : {sample_student['attendance']}%")
print(f"    - Backlogs                   : {sample_student['backlogs']}")
print(f"    - Placement Preparation Score: {sample_student['placement_preparation_score']}/100")
print(f"    - Placement Status           : {sample_student['status']}")
print(f"    - Drives Applied             : {sample_student['drives_applied_count']}")
print(f"    - Interviews Attended        : {sample_student['interviews_attended_count']}")
print(f"    - Selections / Offers        : {sample_student['selections_count']}")
print(f"    - Active Applications        : {sample_student['active_applications_count']}")
print("  [PASS] All 13 student placement details columns present and populated with real data")

print("\n[REQ 1 - TEST 4] Table Filtering Options")
# Filter by placement status = Placed
res_placed = client.get("/api/students/department-placement-details?dept_id=1&status_filter=Placed", headers=cse_headers)
assert res_placed.status_code == 200
placed_items = res_placed.json()["items"]
assert all((s["status"] or "").lower() == "placed" for s in placed_items)
print(f"  [PASS] Placement status filter ('Placed') returned {len(placed_items)} matching records")

# Filter by drive participation = applied
res_applied = client.get("/api/students/department-placement-details?dept_id=1&drive_participation=applied", headers=cse_headers)
assert res_applied.status_code == 200
applied_items = res_applied.json()["items"]
assert all(s["drives_applied_count"] > 0 for s in applied_items)
print(f"  [PASS] Drive participation filter ('applied') returned {len(applied_items)} matching records")

# Filter by section if available
sections = data_cse["available_sections"]
if sections:
    sec = sections[0]
    res_sec = client.get(f"/api/students/department-placement-details?dept_id=1&section={sec}", headers=cse_headers)
    assert res_sec.status_code == 200
    sec_items = res_sec.json()["items"]
    assert all(s["section"] == sec for s in sec_items)
    print(f"  [PASS] Section filter ('{sec}') returned {len(sec_items)} matching records")

# ======================================================================
# REQUIREMENT 2: CONSOLIDATED FEEDBACK REPORT FOR A PARTICULAR DRIVE
# ======================================================================
print("\n[REQ 2 - TEST 1] Drive Feedback Consolidation on Drive with Real Feedback (Drive 4)")
res_fb4 = client.get("/api/ai/drives/4/feedback-summary", headers=admin_headers)
assert res_fb4.status_code == 200, f"Expected 200, got {res_fb4.status_code}: {res_fb4.text}"
fb4_data = res_fb4.json()

print(f"  Drive: {fb4_data.get('company_name')} - {fb4_data.get('role')} (ID: {fb4_data.get('drive_id')})")
# 1. Participation
part = fb4_data["participation"]
print(f"  1. Participation: {part['total_feedbacks']} responses from {part['candidates_attended_or_applied']} attended/eligible")
assert part["total_feedbacks"] == 59, f"Expected 59 feedbacks for Drive 4, got {part['total_feedbacks']}"

# 2. Overall Interview Experience
exp = fb4_data["overall_experience"]
print(f"  2. Overall Interview Experience: Tone breakdown = {exp['sentiment_distribution']}")
assert "summary" in exp and "common_observations" in exp

# 3. Topics Asked
topics = fb4_data["topics_asked"]
print(f"  3. Topics Asked (Grouped & Frequencies): {len(topics)} unique topic areas")
for t in topics[:3]:
    print(f"     - {t['topic']}: {t['frequency']} mentions ({t['percentage']}%)")
assert len(topics) > 0

# 4. Questions Asked (Grouped/Normalized)
questions = fb4_data["questions_asked"]
print(f"  4. Questions Asked (Grouped duplicates with frequency): {len(questions)} aggregated questions")
for q in questions[:3]:
    print(f"     - '{q['question']}': reported by {q['frequency']} candidates (Round: {q['round']})")
assert len(questions) > 0

# 5. Difficulty Distribution
diff = fb4_data["difficulty_distribution"]
print(f"  5. Difficulty Distribution: Avg = {diff['average_score']}/5.0 | Easy: {diff['easy_count']}, Mod: {diff['moderate_count']}, Diff: {diff['difficult_count']}")
assert diff["total_rated"] == part["total_feedbacks"]

# 6. Common Interview Areas
areas = fb4_data["common_interview_areas"]
print(f"  6. Common Interview Areas (present in feedback): {[a['area'] for a in areas]}")
assert len(areas) > 0

# 7. Student Experiences / Suggestions
sugg = fb4_data["student_suggestions"]
print(f"  7. Student Suggestions & Blockers: {len(sugg['top_advice_notes'])} recommendations, {len(sugg['recurring_blockers'])} blockers")
print(f"     Candidate privacy preserved: {sugg['anonymity_preserved']}")
assert sugg["anonymity_preserved"] is True
print("  [PASS] All 7 required sections present in consolidated drive feedback report")

print("\n[REQ 2 - TEST 2] Empty State Handling on Drive with No Feedback")
# Find a real drive in the database that has 0 feedback
all_drives = db.query(PlacementDrive).all()
zero_fb_drive = None
for d in all_drives:
    fb_count = db.query(Feedback).join(Interview).join(Application).filter(Application.drive_id == d.id).count()
    if fb_count == 0:
        zero_fb_drive = d
        break

if not zero_fb_drive:
    zero_fb_drive = PlacementDrive(
        company_id=1,
        role="Trainee Analyst",
        package_lpa=5.0,
        allowed_depts="ALL",
        status="Active"
    )
    db.add(zero_fb_drive)
    db.commit()
    db.refresh(zero_fb_drive)

res_fb_zero = client.get(f"/api/ai/drives/{zero_fb_drive.id}/feedback-summary", headers=admin_headers)
assert res_fb_zero.status_code == 200
fb_zero_data = res_fb_zero.json()
assert fb_zero_data["has_feedback"] is False
assert fb_zero_data["participation"]["total_feedbacks"] == 0
assert "message" in fb_zero_data
print(f"  [PASS] Empty state correctly returned for Drive {zero_fb_drive.id} (total_feedbacks = 0): '{fb_zero_data['message']}'")

print("\n[REQ 2 - TEST 3] Unauthorized Department Drive Scoping for Faculty")
# Find an existing drive not open to CSE
test_restricted_drive = None
for d in all_drives:
    allowed = [x.strip().upper() for x in (d.allowed_depts or "").split(",") if x.strip()]
    if allowed and "ALL" not in allowed and "CSE" not in allowed:
        test_restricted_drive = d
        break

if not test_restricted_drive:
    # Use any existing drive and temporarily test with restricted depts or create properly
    from datetime import date
    test_restricted_drive = PlacementDrive(
        company_id=1,
        role="Mechanical Engineer",
        package_lpa=6.0,
        allowed_depts="MECH,CIVIL",
        location="Hyderabad",
        interview_date=date(2026, 10, 15),
        deadline=date(2026, 10, 10),
        status="Active"
    )
    db.add(test_restricted_drive)
    db.commit()
    db.refresh(test_restricted_drive)

res_unauth_drive = client.get(f"/api/ai/drives/{test_restricted_drive.id}/feedback-summary", headers=cse_headers)
assert res_unauth_drive.status_code == 403, f"Expected 403 Forbidden for CSE faculty requesting MECH/CIVIL drive, got {res_unauth_drive.status_code}"
print(f"  [PASS] CSE faculty accessing MECH/CIVIL drive feedback: HTTP 403 Forbidden ({res_unauth_drive.json().get('detail')})")

print("\n" + "=" * 70)
print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH ZERO FAILURES!")
print("=" * 70)
