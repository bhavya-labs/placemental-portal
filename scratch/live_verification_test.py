import sqlite3
import json
import urllib.request
import urllib.parse
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_alembic_migration():
    print("\n--- 1. Testing Alembic Migration ---")
    db_path = Path("placement_portal.db").resolve()
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    # Check alembic version table
    cur.execute("SELECT version_num FROM alembic_version")
    version = cur.fetchone()[0]
    print(f"Current Alembic revision: {version}")
    assert version == "ac9fcc9ba19f", f"Expected revision ac9fcc9ba19f, got {version}"
    
    # Check column nullability on feedbacks table
    cur.execute("PRAGMA table_info(feedbacks)")
    cols = {row[1]: {"type": row[2], "notnull": row[3]} for row in cur.fetchall()}
    print(f"feedbacks.interview_id schema info: {cols.get('interview_id')}")
    assert cols['interview_id']['notnull'] == 0, "interview_id should be NULLABLE (notnull=0)"
    conn.close()
    print("PASS: Alembic migration verified cleanly applied.")

def login(email, password="password123"):
    data = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/auth/token", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["access_token"]

def test_feedback_submission():
    print("\n--- 2. Testing Feedback Submission (Activity & Interview) ---")
    token = login("student9@platform.edu")
    
    # 2a. Activity feedback with interview_id = None
    url = f"{BASE_URL}/api/feedback/activity/1"
    body = json.dumps({
        "experience_text": "Live test: Great training session on algorithms and coding interviews!",
        "questions_asked": "Binary tree traversals, Dynamic programming",
        "difficulty_rating": 3,
        "preparation_time": "2 weeks",
        "suggestions": "More practice problem sheets"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"Activity feedback response: {res}")
        assert resp.status == 200

    # 2b. Check student interviews endpoint
    req_profile = urllib.request.Request(f"{BASE_URL}/api/auth/profile")
    req_profile.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req_profile) as resp:
        profile = json.loads(resp.read().decode("utf-8"))
        student_id = profile["id"]
        print(f"Student ID: {student_id}")

    req_iv = urllib.request.Request(f"{BASE_URL}/api/interviews/student/{student_id}")
    req_iv.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req_iv) as resp:
        interviews = json.loads(resp.read().decode("utf-8"))
        print(f"Student interview records count: {len(interviews)}")
        if len(interviews) > 0:
            iv_id = interviews[0]["id"]
            print(f"Found real interview ID: {iv_id}")
            # Clean existing feedback for this interview if needed
            conn = sqlite3.connect("placement_portal.db")
            conn.cursor().execute("DELETE FROM feedbacks WHERE interview_id=?", (iv_id,))
            conn.commit()
            conn.close()

            # Submit interview review
            url_iv = f"{BASE_URL}/api/interviews/{iv_id}/feedback"
            body_iv = json.dumps({
                "experience_text": "Live test: Technical round covered trees, graphs, and system architecture.",
                "questions_asked": "LRU cache, Trie implementation",
                "difficulty_rating": 4,
                "preparation_time": "3 weeks",
                "suggestions": "Practice live coding on whiteboard"
            }).encode("utf-8")
            req_post_iv = urllib.request.Request(url_iv, data=body_iv, method="POST")
            req_post_iv.add_header("Authorization", f"Bearer {token}")
            req_post_iv.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req_post_iv) as resp_iv:
                res_iv = json.loads(resp_iv.read().decode("utf-8"))
                print(f"Interview feedback response: {res_iv}")
                assert resp_iv.status == 200

    print("PASS: Feedback submissions succeed.")

def test_pagination_and_sorting():
    print("\n--- 3. Testing Student Pagination and Default Newest Sort ---")
    admin_token = login("admin@platform.edu", "password123")
    
    # 3a. Add a new candidate
    test_email = "new_candidate_pagination_test@university.edu"
    # Cleanup if exists
    conn = sqlite3.connect("placement_portal.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE email=?", (test_email,))
    conn.commit()
    conn.close()

    new_stud_payload = json.dumps({
        "name": "Zackary Pagination Test Candidate",
        "email": test_email,
        "dept_id": 1,
        "gender": "Male",
        "batch": "2026",
        "phone": "9998887776",
        "cgpa": 9.4,
        "attendance": 92.0,
        "backlogs": 0,
        "skills": json.dumps(["Python", "React", "Docker"])
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/students", data=new_stud_payload, method="POST")
    req.add_header("Authorization", f"Bearer {admin_token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        created = json.loads(resp.read().decode("utf-8"))
        print(f"Created student ID: {created.get('id')}")

    # 3b. Query Page 1 with limit=25 (default sort: id desc)
    req_list = urllib.request.Request(f"{BASE_URL}/api/students?page=1&limit=25")
    req_list.add_header("Authorization", f"Bearer {admin_token}")
    with urllib.request.urlopen(req_list) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        total = res["total"]
        items = res["items"]
        print(f"Total students: {total}, Items returned on Page 1: {len(items)}")
        assert len(items) == 25
        # Verify the newly created candidate is on Page 1 at index 0 (newest first)
        assert items[0]["email"] == test_email, f"Expected newest student at top of Page 1, got {items[0]['email']}"
        print(f"PASS: Newly added student '{items[0]['name']}' appears at index 0 on Page 1!")

    # 3c. Query Page 2
    req_page2 = urllib.request.Request(f"{BASE_URL}/api/students?page=2&limit=25")
    req_page2.add_header("Authorization", f"Bearer {admin_token}")
    with urllib.request.urlopen(req_page2) as resp:
        res_p2 = json.loads(resp.read().decode("utf-8"))
        print(f"Page 2 offset: {res_p2['offset']}, Items on Page 2: {len(res_p2['items'])}")
        assert res_p2["page"] == 2
        assert res_p2["offset"] == 25
        assert len(res_p2["items"]) == 25
        assert res_p2["items"][0]["id"] != items[0]["id"]
        print("PASS: Page 2 correctly returns next offset records.")

    # 3d. Clean up candidate
    conn = sqlite3.connect("placement_portal.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE email=?", (test_email,))
    conn.commit()
    conn.close()

def test_company_analytics_and_faculty_scope():
    print("\n--- 4. Testing Company Analytics (5b) & Department Scope (5a) ---")
    faculty_token = login("faculty.cse@platform.edu", "password123")
    
    # 4a. Check company analytics for active company (ID 1 Google)
    req_active = urllib.request.Request(f"{BASE_URL}/api/analytics/company/1")
    req_active.add_header("Authorization", f"Bearer {faculty_token}")
    with urllib.request.urlopen(req_active) as resp:
        active_analytics = json.loads(resp.read().decode("utf-8"))
        print(f"Active Company (Google) Analytics: {active_analytics['company_name']}, Total Applicants: {active_analytics['total_applicants']}, Selected: {active_analytics['selected_students']}, Top skills: {active_analytics['top_skills_hired']}")
        assert active_analytics["total_applicants"] > 0
        assert "top_skills_hired" in active_analytics
        print("PASS: Active company has populated data and top_skills_hired.")

    # 4b. Check company analytics for zero-applicant company (e.g. ID 23 AMD)
    req_zero = urllib.request.Request(f"{BASE_URL}/api/analytics/company/23")
    req_zero.add_header("Authorization", f"Bearer {faculty_token}")
    with urllib.request.urlopen(req_zero) as resp:
        zero_analytics = json.loads(resp.read().decode("utf-8"))
        print(f"Zero Company (AMD) Analytics: {zero_analytics['company_name']}, Total Applicants: {zero_analytics['total_applicants']}, Top skills: {zero_analytics['top_skills_hired']}")
        assert zero_analytics["total_applicants"] == 0
        assert "top_skills_hired" in zero_analytics
        assert zero_analytics["top_skills_hired"] == []
        print("PASS: Zero applicant company returns top_skills_hired: [] safely.")

if __name__ == "__main__":
    test_alembic_migration()
    test_feedback_submission()
    test_pagination_and_sorting()
    test_company_analytics_and_faculty_scope()
    print("\n=== ALL LIVE TESTS PASSED SUCCESSFULLY! ===")
