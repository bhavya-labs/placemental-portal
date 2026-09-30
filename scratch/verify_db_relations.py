import os
import sys
from sqlalchemy import func

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.app.database import SessionLocal
from backend.app.models import Student, Parent, Department, PlacementDrive, Application, Notification, User

def run_integrity_audit():
    print("--- DATABASE RELATIONSHIPS & LOGICAL INTEGRITY AUDIT ---")
    db = SessionLocal()
    try:
        # 1. Check departments mapped to students
        invalid_depts = db.query(Student).filter(~Student.dept_id.in_(db.query(Department.id))).all()
        print(f"Invalid Department references on Students: {len(invalid_depts)}")
        assert len(invalid_depts) == 0, "Found students with invalid department IDs!"

        # 2. Check parent-child relationships
        invalid_parent_wards = db.query(Parent).filter(~Parent.student_id.in_(db.query(Student.id))).all()
        print(f"Invalid Parent-Ward references: {len(invalid_parent_wards)}")
        assert len(invalid_parent_wards) == 0, "Found parents with invalid child student IDs!"

        # 3. Check duplicate applications
        dupes = db.query(
            Application.student_id, Application.drive_id, func.count(Application.id).label('cnt')
        ).group_by(Application.student_id, Application.drive_id).having(func.count(Application.id) > 1).all()
        print(f"Duplicate Applications (same student to same drive): {len(dupes)}")
        assert len(dupes) == 0, "Found duplicate student applications!"

        # 4. Check duplicate student profile IDs
        student_dupes = db.query(
            Student.id, func.count(Student.id).label('cnt')
        ).group_by(Student.id).having(func.count(Student.id) > 1).all()
        print(f"Duplicate Student IDs in students table: {len(student_dupes)}")
        assert len(student_dupes) == 0, "Found duplicate students in profiles table!"

        # 5. Check student batch years format (all should be e.g. 2025, 2026, 2027)
        invalid_batches = db.query(Student).filter(~Student.batch.in_(["2025", "2026", "2027"])).all()
        print(f"Students with invalid batch formats: {len(invalid_batches)}")
        assert len(invalid_batches) == 0, "Found students with non-standard batch strings!"

        # 6. Check notifications integrity
        invalid_notifs = db.query(Notification).filter(~Notification.user_id.in_(db.query(User.id))).all()
        print(f"Orphan Notification user references: {len(invalid_notifs)}")
        assert len(invalid_notifs) == 0, "Found orphan notification entries!"

        print("\nALL DATABASE LOGICAL INTEGRITY CHECKS PASSED SUCCESSFULLY!")
    finally:
        db.close()

if __name__ == '__main__':
    run_integrity_audit()
