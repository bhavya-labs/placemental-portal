from backend.app.database import SessionLocal
from backend.app.models import Student, User

db = SessionLocal()
try:
    total_students = db.query(Student).count()
    total_users = db.query(User).filter(User.role == "student").count()
    print(f"Total students in DB: {total_students}")
    print(f"Total student users in DB: {total_users}")
finally:
    db.close()
