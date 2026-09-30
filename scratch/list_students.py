import os
import sys

# Insert project root to path
project_root = "d:\\placement portal"
sys.path.insert(0, project_root)

from backend.app.database import SessionLocal
from backend.app.models import Student, User

db = SessionLocal()
try:
    students = db.query(Student).join(User).all()
    print("Database Student List:")
    for s in students[:10]:
        print(f"ID: {s.id} | Name: {s.user.name} | Email: {s.user.email} | Verification Status: {s.verification_status}")
finally:
    db.close()
