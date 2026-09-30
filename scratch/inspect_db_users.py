import os
import sys

# Insert project root to path
project_root = "d:\\placement portal"
sys.path.insert(0, project_root)

from backend.app.database import SessionLocal
from backend.app.models import Student, User

db = SessionLocal()
try:
    print("USER TABLE:")
    users = db.query(User).filter(User.role == "student").all()
    for u in users[:10]:
        print(f"User ID: {u.id} | Name: {u.name} | Email: {u.email}")
        
    print("\nSTUDENT TABLE:")
    students = db.query(Student).all()
    for s in students[:10]:
        print(f"Student ID: {s.id} | Verification Status: {s.verification_status}")
finally:
    db.close()
