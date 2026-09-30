from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, Student, PlacementActivity, ActivityAttendance, PlacementDrive, Department, SystemLog, Parent
from backend.app.schemas import PlacementActivityCreate, PlacementActivityResponse, ActivityAttendanceMark, ActivityAttendanceResponse
from backend.app.auth import get_current_user, verify_permission
from typing import List, Optional

router = APIRouter(prefix="/api/activities", tags=["Placement Activities"])

@router.get("", response_model=List[PlacementActivityResponse])
def list_activities(
    placement_drive_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(PlacementActivity)
    if placement_drive_id:
        query = query.filter(PlacementActivity.placement_drive_id == placement_drive_id)
        
    activities = query.all()
    
    if current_user.role in ["admin", "tnp"]:
        return activities

    # Find the user's department/batch scope
    user_dept_code = None
    user_batch = None
    if current_user.role == "student":
        student = current_user.student_profile
        if student:
            user_dept_code = student.department.code.upper()
            user_batch = student.batch
    elif current_user.role == "parent":
        parent = db.query(Parent).filter(Parent.id == current_user.id).first()
        if parent:
            student = db.query(Student).filter(Student.id == parent.student_id).first()
            if student:
                user_dept_code = student.department.code.upper()
                user_batch = student.batch

    faculty_scope = None
    faculty_scope_value = None
    if current_user.role in ["faculty", "hod"]:
        try:
            scope_info = verify_permission(current_user, "Placement Drives", "VIEW", db)
            faculty_scope = scope_info.get("scope")
            faculty_scope_value = scope_info.get("scope_value")
        except HTTPException:
            faculty_scope = "NONE"

    visible_activities = []
    for act in activities:
        if act.placement_drive_id:
            d = act.drive
            if not d:
                continue
            is_visible = False
            allowed_depts = [dept.strip().upper() for dept in d.allowed_depts.split(",")]
            
            if current_user.role in ["student", "parent"]:
                if user_dept_code and (user_dept_code in allowed_depts or "ALL" in allowed_depts):
                    if not d.batch or d.batch == user_batch:
                        is_visible = True
            elif current_user.role in ["faculty", "hod"]:
                if faculty_scope == "ALL":
                    is_visible = True
                elif faculty_scope == "DEPARTMENT":
                    if faculty_scope_value and faculty_scope_value.upper() in allowed_depts:
                        is_visible = True
                elif faculty_scope == "SECTION":
                    f_profile = current_user.faculty_profile
                    if f_profile:
                        f_dept_code = f_profile.department.code.upper()
                        if f_dept_code in allowed_depts:
                            is_visible = True
            if is_visible:
                visible_activities.append(act)
        else:
            visible_activities.append(act)
            
    return visible_activities

@router.post("", response_model=PlacementActivityResponse)
def create_activity(
    payload: PlacementActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_permission(current_user, "Placement Drives", "CREATE", db)
    
    activity = PlacementActivity(**payload.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)

    # Notify students of the scheduled training & create a reminder (Req 12)
    from backend.app.models import Notification
    students = db.query(Student).all()
    for s in students:
        db.add(Notification(
            user_id=s.id,
            title="New Training Activity Scheduled",
            message=f"A new training activity '{activity.activity_name}' ({activity.activity_type}) has been scheduled for {activity.date.strftime('%Y-%m-%d')}."
        ))
        db.add(Notification(
            user_id=s.id,
            title="Training Reminder",
            message=f"Reminder: You have a scheduled training activity '{activity.activity_name}' on {activity.date.strftime('%Y-%m-%d')}. Attendance is mandatory."
        ))
    db.commit()

    return activity

@router.get("/{activity_id}", response_model=PlacementActivityResponse)
def get_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    activity = db.query(PlacementActivity).filter(PlacementActivity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

@router.put("/{activity_id}", response_model=PlacementActivityResponse)
def update_activity(
    activity_id: int,
    payload: PlacementActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_permission(current_user, "Placement Drives", "EDIT", db)
    activity = db.query(PlacementActivity).filter(PlacementActivity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    for k, v in payload.model_dump().items():
        setattr(activity, k, v)
        
    db.commit()
    db.refresh(activity)
    return activity

@router.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_permission(current_user, "Placement Drives", "DELETE", db)
    activity = db.query(PlacementActivity).filter(PlacementActivity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    db.delete(activity)
    db.commit()
    return {"message": "Activity deleted successfully"}

# ATTENDANCE MANAGEMENT
@router.get("/{activity_id}/attendance", response_model=List[ActivityAttendanceResponse])
def get_activity_attendance(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only TNP, Faculty, Admin can check attendance
    if current_user.role not in ["admin", "tnp", "faculty", "hod"]:
         raise HTTPException(status_code=403, detail="Access denied")

    activity = db.query(PlacementActivity).filter(PlacementActivity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Scoping for Faculty/HOD
    if current_user.role in ["faculty", "hod"]:
        scope_info = verify_permission(current_user, "Student Performance", "VIEW", db)
        # Filter attendance list according to scope
        query = db.query(ActivityAttendance).filter(ActivityAttendance.activity_id == activity_id)
        if scope_info["scope"] == "DEPARTMENT":
            query = query.join(Student).join(Department).filter(Department.code == scope_info["scope_value"])
        elif scope_info["scope"] == "SECTION":
            query = query.join(Student).filter(Student.section == scope_info["scope_value"])
        return query.all()

    return db.query(ActivityAttendance).filter(ActivityAttendance.activity_id == activity_id).all()

@router.post("/{activity_id}/attendance")
def mark_activity_attendance(
    activity_id: int,
    payload: List[ActivityAttendanceMark],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_permission(current_user, "Placement Drives", "EDIT", db)
    
    activity = db.query(PlacementActivity).filter(PlacementActivity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    for att in payload:
        # Check if attendance record already exists
        record = db.query(ActivityAttendance).filter(
            ActivityAttendance.activity_id == activity_id,
            ActivityAttendance.student_id == att.student_id
        ).first()

        if record:
            record.status = att.status
            record.remarks = att.remarks
        else:
            record = ActivityAttendance(
                activity_id=activity_id,
                student_id=att.student_id,
                status=att.status,
                remarks=att.remarks
            )
            db.add(record)

    db.commit()

    # Audit Logging (Req 13)
    log = SystemLog(
        user_email=current_user.email,
        action="UPDATE_ACTIVITY_ATTENDANCE",
        details=f"Updated attendance for Activity ID {activity_id} (marked {len(payload)} students)."
    )
    db.add(log)
    db.commit()

    return {"message": "Attendance successfully updated"}
