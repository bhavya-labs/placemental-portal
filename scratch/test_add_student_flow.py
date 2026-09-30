from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User, Student
from backend.app.auth import create_access_token
import uuid

client = TestClient(app)
admin_token = create_access_token(data={"sub": "admin@platform.edu", "role": "admin"})
headers = {"Authorization": f"Bearer {admin_token}"}

test_email = f"test_add_{uuid.uuid4().hex[:6]}@student.edu"
test_name = "Zoe TestStudent"

payload = {
    "name": test_name,
    "email": test_email,
    "dept_id": 1,
    "gender": "Female",
    "batch": "2026",
    "phone": "9998887776",
    "cgpa": 8.5,
    "attendance": 90.0,
    "backlogs": 0,
    "skills": "[\"Python\", \"FastAPI\"]"
}

# 1. POST /api/students
create_resp = client.post("/api/students", json=payload, headers=headers)
print("Create Status:", create_resp.status_code)
print("Create Response:", create_resp.json())

# 2. Check direct database query
db = SessionLocal()
try:
    db_student = db.query(User).filter(User.email == test_email).first()
    print("Database Query Check:")
    if db_student:
        print(f"FOUND IN DB: User ID {db_student.id}, Name {db_student.name}")
        profile = db.query(Student).filter(Student.id == db_student.id).first()
        print(f"Student Profile: Dept {profile.dept_id}, CGPA {profile.cgpa}, Readiness {profile.readiness_score}")
    else:
        print("NOT FOUND IN DB!")
finally:
    db.close()

# 3. Check GET /api/students (default list call from frontend)
# Default frontend call: limit=1000, sort_by=name, sort_order=asc
list_resp = client.get("/api/students?limit=1000", headers=headers)
data = list_resp.json()
print("\nGET /api/students Check:")
print(f"Total returned items: {len(data['items'])}, Total in DB reported: {data['total']}")
found_in_items = any(s["email"] == test_email for s in data["items"])
print(f"Is '{test_name}' in the returned items? {found_in_items}")

# 4. Check if searching by name finds it
search_resp = client.get(f"/api/students?search={test_name}", headers=headers)
search_data = search_resp.json()
found_in_search = any(s["email"] == test_email for s in search_data["items"])
print(f"Is '{test_name}' in search results? {found_in_search}")
