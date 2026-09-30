from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Student, ActivityAttendance, User
from backend.app.auth import get_current_user, verify_permission, enforce_student_scope
from typing import List

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

@router.get("/academic/{student_id}")
def get_academic_attendance(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = enforce_student_scope(current_user, student_id, db, "VIEW")

    return {
        "student_id": student.id,
        "name": student.user.name,
        "academic_attendance_percentage": student.attendance
    }

@router.get("/activity/student/{student_id}")
def get_activity_attendance(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = enforce_student_scope(current_user, student_id, db, "VIEW")

    records = db.query(ActivityAttendance).filter(ActivityAttendance.student_id == student_id).all()
    
    results = []
    for rec in records:
        results.append({
            "id": rec.id,
            "activity_id": rec.activity_id,
            "activity_name": rec.activity.activity_name if rec.activity else "Unknown Activity",
            "activity_type": rec.activity.activity_type if rec.activity else "N/A",
            "date": rec.activity.date if rec.activity else None,
            "status": rec.status,
            "remarks": rec.remarks
        })
    return results
