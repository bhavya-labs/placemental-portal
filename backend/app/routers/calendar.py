from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, Student, PlacementDrive, Interview, PlacementActivity, Parent, Application
from backend.app.auth import get_current_user, get_permitted_student_query, verify_permission
from typing import List, Dict, Any
from datetime import datetime, date, timedelta

router = APIRouter(prefix="/api/calendar", tags=["Placement Calendar"])

@router.get("/events")
def get_calendar_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Expose scoped placement calendar events (drives, deadlines, training, interview slots).
    Enforces student parent-scoping, self-scoping, and HOD/Faculty scoping on student interview listings.
    """
    events = []

    # 1. Scoped Placement Drives
    drives = db.query(PlacementDrive).all()
    visible_drive_ids = set()
    visible_drives = []

    # Get user role department and batch
    user_dept_code = None
    user_batch = None
    student = None
    applied_drive_ids = set()
    if current_user.role == "student":
        student = current_user.student_profile
        if student:
            user_dept_code = student.department.code.upper()
            user_batch = student.batch
            applied_drive_ids = {a.drive_id for a in db.query(Application.drive_id).filter(Application.student_id == student.id).all()}
    elif current_user.role == "parent":
        parent = db.query(Parent).filter(Parent.id == current_user.id).first()
        if parent:
            student = db.query(Student).filter(Student.id == parent.student_id).first()
            if student:
                user_dept_code = student.department.code.upper()
                user_batch = student.batch
                applied_drive_ids = {a.drive_id for a in db.query(Application.drive_id).filter(Application.student_id == student.id).all()}

    faculty_scope = None
    faculty_scope_value = None
    if current_user.role in ["faculty", "hod"]:
        try:
            scope_info = verify_permission(current_user, "Placement Drives", "VIEW", db)
            faculty_scope = scope_info.get("scope")
            faculty_scope_value = scope_info.get("scope_value")
        except HTTPException:
            faculty_scope = "NONE"

    for d in drives:
        is_visible = False
        allowed_depts = [dept.strip().upper() for dept in (d.allowed_depts or "").split(",")]
        
        if current_user.role in ["admin", "tnp"]:
            is_visible = True
        elif current_user.role in ["student", "parent"]:
            if d.id in applied_drive_ids:
                is_visible = True
            elif student and user_dept_code and (user_dept_code in allowed_depts or "ALL" in allowed_depts):
                if (not d.batch or d.batch == user_batch) and \
                   (student.cgpa >= (d.cgpa_cutoff or 0.0)) and \
                   (student.backlogs <= (d.allowed_backlogs if d.allowed_backlogs is not None else 999)) and \
                   (student.attendance >= (d.min_attendance or 0.0)):
                    is_visible = True
        elif current_user.role in ["faculty", "hod"]:
            if faculty_scope == "ALL":
                is_visible = True
            elif faculty_scope == "DEPARTMENT":
                scope_code = str(faculty_scope_value).upper() if faculty_scope_value else ""
                if scope_code.isdigit():
                    from backend.app.models import Department
                    d_obj = db.query(Department).filter(Department.id == int(scope_code)).first()
                    if d_obj:
                        scope_code = d_obj.code.upper()
                if "ALL" in allowed_depts or scope_code in allowed_depts:
                    is_visible = True
            elif faculty_scope == "SECTION":
                f_profile = current_user.faculty_profile
                if f_profile:
                    f_dept_code = f_profile.department.code.upper()
                    if f_dept_code in allowed_depts:
                        is_visible = True

        if is_visible:
            visible_drive_ids.add(d.id)
            visible_drives.append(d)

    for d in visible_drives:
        # Drive Deadline Event
        events.append({
            "id": f"drive-deadline-{d.id}",
            "title": f"Deadline: {d.company.name} ({d.role})",
            "start": d.deadline.isoformat(),
            "end": d.deadline.isoformat(),
            "allDay": True,
            "type": "deadline",
            "color": "#ef4444",  # Red for deadlines
            "details": f"Apply before deadline. CGPA Cutoff: {d.cgpa_cutoff}."
        })
        # Drive Interview Date Event
        events.append({
            "id": f"drive-interview-{d.id}",
            "title": f"Drives: {d.company.name} Interviews",
            "start": d.interview_date.isoformat(),
            "end": d.interview_date.isoformat(),
            "allDay": True,
            "type": "drive",
            "color": "#3b82f6",  # Blue for drives
            "details": f"Hiring for role '{d.role}' (Package: {d.package_lpa} LPA)."
        })

    # 2. Scoped Student Interview Events
    student_query = get_permitted_student_query(current_user, db, "VIEW")
    permitted_student_ids = [s.id for s in student_query.all()]
    
    interviews = db.query(Interview).filter(Interview.student_id.in_(permitted_student_ids)).all()
    for iv in interviews:
        # Determine date start/end ISO strings
        start_dt = iv.interview_date
        end_dt = start_dt + timedelta(hours=1)
        
        events.append({
            "id": f"interview-{iv.id}",
            "title": f"Interview: {iv.round_name} - {iv.application.student.user.name}",
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "allDay": False,
            "type": "interview",
            "color": "#10b981",  # Green for interviews
            "details": f"Company: {iv.application.drive.company.name}. Status: {iv.status}."
        })

    # 3. Placement Activities (Workshops, Training, Tests, Talks)
    activities = db.query(PlacementActivity).all()
    for act in activities:
        if act.placement_drive_id and act.placement_drive_id not in visible_drive_ids:
            continue
            
        events.append({
            "id": f"activity-{act.id}",
            "title": f"Event: {act.activity_name} ({act.activity_type})",
            "start": act.date.isoformat(),
            "end": act.date.isoformat(),
            "allDay": True,
            "type": "activity",
            "color": "#f59e0b",  # Orange for activities
            "details": f"Mode/Venue: {act.location}."
        })

    return events
