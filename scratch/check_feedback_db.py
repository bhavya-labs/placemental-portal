from backend.app.database import SessionLocal
from backend.app.models import User, Student, Interview, Feedback, Application

db = SessionLocal()
try:
    print("--- Users (students) ---")
    students = db.query(User).filter(User.role == "student").all()
    for s in students[:5]:
        print(f"User ID: {s.id}, Name: {s.name}, Email: {s.email}")

    print("\n--- Interviews ---")
    interviews = db.query(Interview).all()
    print(f"Total interviews: {len(interviews)}")
    for i in interviews[:10]:
        has_fb = db.query(Feedback).filter(Feedback.interview_id == i.id).first()
        print(f"Interview ID: {i.id}, Student ID: {i.student_id}, Round: {i.round_name}, Has Feedback: {has_fb is not None}")

    print("\n--- Feedback count ---")
    feedbacks = db.query(Feedback).all()
    print(f"Total feedbacks: {len(feedbacks)}")
    for fb in feedbacks[:5]:
        print(f"Feedback ID: {fb.id}, Interview ID: {fb.interview_id}, Activity ID: {fb.activity_id}")
finally:
    db.close()
