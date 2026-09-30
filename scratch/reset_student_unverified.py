import os
import sys

# Insert project root to path
project_root = "d:\\placement portal"
sys.path.insert(0, project_root)

from backend.app.database import SessionLocal
from backend.app.models import Student, User

db = SessionLocal()
try:
    student = db.query(Student).join(User).filter(User.email == "student1@platform.edu").first()
    if student:
        print(f"Found student {student.user.name} (ID: {student.id})")
        print(f"Current verification status: {student.verification_status}")
        
        # Reset status and other fields to simulate uncompleted profile
        student.verification_status = "UNVERIFIED"
        student.profile_completed = False
        student.cgpa = 0.0
        student.attendance = 0.0
        student.backlogs = 0
        db.commit()
        print("Successfully reset student to UNVERIFIED for manual browser testing.")
    else:
        print("Student student1@platform.edu not found!")
finally:
    db.close()
