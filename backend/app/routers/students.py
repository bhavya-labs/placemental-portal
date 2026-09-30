import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from backend.app.database import get_db
from backend.app.models import User, Student, Department, SystemLog, CorrectionRequest, Application, Interview, Feedback, PlacementDrive, Parent, ActivityAttendance
from backend.app.schemas import StudentResponse, StudentUpdate, UserResponse, CorrectionRequestCreate, CorrectionRequestResponse, CorrectionRequestAction
from backend.app.auth import get_current_user, get_password_hash, get_current_faculty, get_permitted_student_query, enforce_student_scope
from backend.app.ml.predictor import predictor

router = APIRouter(prefix="/api/students", tags=["Students"])

@router.get("")
@router.get("/list")
def get_students(
    search: Optional[str] = None,
    dept_id: Optional[int] = None,
    batch: Optional[str] = None,
    status_filter: Optional[str] = None,
    gender: Optional[str] = None,
    cgpa_min: Optional[float] = None,
    skills: Optional[str] = None,
    sort_by: Optional[str] = "id",
    sort_order: Optional[str] = "desc",
    page: int = 1,
    limit: int = 20,
    offset: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only faculty, HOD, TNP, and admins can query student lists
    if current_user.role not in ["faculty", "admin", "hod", "tnp"]:
        raise HTTPException(status_code=403, detail="Access denied")

    query = get_permitted_student_query(current_user, db, "VIEW").join(User)

    # Filters
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    if dept_id:
        query = query.filter(Student.dept_id == dept_id)
        
    if batch:
        query = query.filter(Student.batch == batch)
        
    if status_filter:
        norm_status = "At Risk" if status_filter.lower().replace("_", " ") == "at risk" else status_filter
        query = query.filter(Student.status.ilike(norm_status))

    if gender:
        query = query.filter(Student.gender == gender)
        
    if cgpa_min:
        query = query.filter(Student.cgpa >= cgpa_min)
        
    if skills:
        # Check if skills contain matching term
        skills_search = [s.strip().lower() for s in skills.split(",")]
        for sk in skills_search:
            query = query.filter(Student.skills.ilike(f"%{sk}%"))

    # Sorting: default to newest students (id/created_at desc)
    if sort_by == "name":
        order_col = User.name
    elif sort_by == "cgpa":
        order_col = Student.cgpa
    elif sort_by == "readiness_score":
        order_col = Student.readiness_score
    elif sort_by == "placement_probability":
        order_col = Student.placement_probability
    elif sort_by in ["created_at", "id"]:
        order_col = Student.id
    else:
        order_col = Student.id

    if sort_order == "asc":
        query = query.order_by(asc(order_col))
    else:
        query = query.order_by(desc(order_col))

    # Pagination: cap safe limit at 200 as secondary safety margin
    total = query.count()
    safe_limit = min(max(limit, 1), 200)
    actual_offset = offset if (offset is not None and offset >= 0) else (max(page, 1) - 1) * safe_limit
    items = query.offset(actual_offset).limit(safe_limit).all()

    # Build response data structures
    students_list = []
    for s in items:
        students_list.append({
            "id": s.id,
            "name": s.user.name,
            "email": s.user.email,
            "dept_id": s.dept_id,
            "dept_code": s.department.code,
            "dept_name": s.department.name,
            "gender": s.gender,
            "batch": s.batch,
            "phone": s.phone,
            "cgpa": s.cgpa,
            "attendance": s.attendance,
            "backlogs": s.backlogs,
            "status": s.status,
            "readiness_score": s.readiness_score,
            "placement_probability": s.placement_probability,
            "skills": s.skills,
            "leetcode_score": s.leetcode_score,
            "codechef_score": s.codechef_score,
            "hackerrank_score": s.hackerrank_score,
            "profile_completed": s.profile_completed,
            "section": s.section
        })

    return {
        "total": total,
        "page": page,
        "limit": safe_limit,
        "offset": actual_offset,
        "items": students_list
    }

@router.get("/department-placement-details")
def get_department_placement_details(
    dept_id: Optional[int] = None,
    batch: Optional[str] = "2026",
    section: Optional[str] = None,
    status_filter: Optional[str] = None,
    drive_participation: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Department-filtered student placement details view for Faculty/HOD and Admins.
    Provides student-wise placement metrics and department-level summary cards.
    Strictly enforces department RBAC: faculty/HOD can only access their authorized department.
    """
    if current_user.role not in ["faculty", "hod", "admin", "tnp"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # 1. Department authorization & scoping
    if current_user.role in ["faculty", "hod"]:
        f_profile = current_user.faculty_profile
        user_dept_id = f_profile.dept_id if f_profile else None
        if not user_dept_id:
            raise HTTPException(status_code=403, detail="Faculty profile has no assigned department")
        
        # If user explicitly requested a dept_id different from their own, verify elevated grant
        if dept_id is not None and int(dept_id) != user_dept_id:
            from backend.app.auth import verify_permission
            scope_info = verify_permission(current_user, "Student Performance", "VIEW", db)
            scope = scope_info.get("scope")
            scope_val = str(scope_info.get("scope_value", "")).upper()
            target_dept = db.query(Department).filter(Department.id == int(dept_id)).first()
            if scope != "ALL" and (not target_dept or scope_val not in [str(dept_id), target_dept.code.upper()]):
                raise HTTPException(status_code=403, detail="Access denied: unauthorized department scope")
            target_dept_id = int(dept_id)
        else:
            target_dept_id = user_dept_id
    else:
        target_dept_id = int(dept_id) if dept_id else 1

    department = db.query(Department).filter(Department.id == target_dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # 2. Base query for department students
    base_students_query = db.query(Student).join(User).filter(Student.dept_id == target_dept_id)
    if batch:
        base_students_query = base_students_query.filter(Student.batch == batch)

    all_dept_students = base_students_query.all()
    all_student_ids = [s.id for s in all_dept_students]

    # Pre-fetch applications & interviews for accurate calculation
    dept_applications = (
        db.query(Application)
        .filter(Application.student_id.in_(all_student_ids))
        .all()
        if all_student_ids else []
    )
    dept_interviews = (
        db.query(Interview)
        .filter(Interview.student_id.in_(all_student_ids))
        .all()
        if all_student_ids else []
    )

    student_apps_map = {}
    for app in dept_applications:
        student_apps_map.setdefault(app.student_id, []).append(app)

    student_interviews_map = {}
    for iv in dept_interviews:
        student_interviews_map.setdefault(iv.student_id, []).append(iv)

    # 3. Compute Department-level summary cards/counts
    total_students = len(all_dept_students)
    placed_students = sum(1 for s in all_dept_students if s.status == "Placed")
    at_risk_students = sum(1 for s in all_dept_students if s.status == "At Risk")
    unplaced_students = total_students - placed_students

    students_with_apps = {s_id for s_id, apps in student_apps_map.items() if len(apps) > 0}
    students_participated = sum(1 for s in all_dept_students if s.id in students_with_apps)
    students_not_participated = total_students - students_participated

    total_applications = len(dept_applications)
    total_selections = sum(1 for a in dept_applications if a.status == "Selected")

    summary = {
        "total_students": total_students,
        "placed_students": placed_students,
        "unplaced_students": unplaced_students,
        "at_risk_students": at_risk_students,
        "placement_percentage": round((placed_students / total_students * 100), 1) if total_students > 0 else 0.0,
        "students_participated": students_participated,
        "students_not_participated": students_not_participated,
        "total_applications": total_applications,
        "total_selections": total_selections
    }

    # 4. Apply Table Filters
    filtered_students = all_dept_students

    if section:
        filtered_students = [s for s in filtered_students if (s.section or "").upper() == section.upper()]

    if status_filter:
        norm_filter = "at risk" if status_filter.lower().replace("_", " ") == "at risk" else status_filter.lower()
        filtered_students = [s for s in filtered_students if (s.status or "").lower() == norm_filter]

    if drive_participation == "applied":
        filtered_students = [s for s in filtered_students if s.id in students_with_apps]
    elif drive_participation == "not_applied":
        filtered_students = [s for s in filtered_students if s.id not in students_with_apps]

    if search:
        search_term = search.lower().strip()
        filtered_students = [
            s for s in filtered_students
            if search_term in (s.user.name or "").lower()
            or search_term in (s.user.email or "").lower()
            or search_term in str(s.id)
            or search_term in f"{department.code}-{s.id}".lower()
        ]

    available_sections = sorted(list({s.section for s in all_dept_students if s.section}))

    # 5. Pagination
    safe_limit = max(1, min(limit, 200))
    total_filtered = len(filtered_students)
    total_pages = (total_filtered + safe_limit - 1) // safe_limit
    safe_page = max(1, page)
    offset = (safe_page - 1) * safe_limit
    paged_students = filtered_students[offset : offset + safe_limit]

    # 6. Format student items
    terminal_statuses = {"rejected", "selected", "withdrawn"}
    students_list = []
    for s in paged_students:
        s_apps = student_apps_map.get(s.id, [])
        s_interviews = student_interviews_map.get(s.id, [])
        selections_count = sum(1 for a in s_apps if a.status == "Selected")
        active_apps_count = sum(1 for a in s_apps if (a.status or "").lower() not in terminal_statuses)

        students_list.append({
            "id": s.id,
            "roll_no": f"{department.code}-{s.id:03d}",
            "name": s.user.name,
            "email": s.user.email,
            "branch": department.code,
            "dept_name": department.name,
            "section": s.section or "A",
            "batch": s.batch,
            "cgpa": s.cgpa,
            "attendance": s.attendance,
            "backlogs": s.backlogs,
            "placement_preparation_score": round(s.readiness_score, 1) if s.readiness_score is not None else 0.0,
            "readiness_score": s.readiness_score,
            "status": s.status or "Unplaced",
            "drives_applied_count": len(s_apps),
            "interviews_attended_count": len(s_interviews),
            "selections_count": selections_count,
            "active_applications_count": active_apps_count
        })

    return {
        "department": {
            "id": department.id,
            "code": department.code,
            "name": department.name
        },
        "summary": summary,
        "available_sections": available_sections,
        "total": total_filtered,
        "page": safe_page,
        "limit": safe_limit,
        "total_pages": total_pages,
        "students": students_list,
        "items": students_list
    }

# Singular alias router to satisfy /api/student/list routing
student_alias_router = APIRouter(prefix="/api/student", tags=["Students"])
student_alias_router.add_api_route("/list", get_students, methods=["GET"])

# CORRECTION REQUESTS
@router.post("/correction-requests", response_model=CorrectionRequestResponse)
def create_correction_request(
    payload: CorrectionRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "student" or not current_user.student_profile:
        raise HTTPException(status_code=403, detail="Only students can submit correction requests")
        
    req = CorrectionRequest(
        student_id=current_user.id,
        field=payload.field,
        current_value=payload.current_value,
        requested_value=payload.requested_value,
        reason=payload.reason,
        status="Pending"
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    # Trigger notifications (Req 12)
    from backend.app.models import Notification
    db.add(Notification(
        user_id=current_user.id,
        title="Correction Request Submitted",
        message=f"Your profile correction request for field '{payload.field}' has been submitted and is pending review."
    ))
    
    staff_members = db.query(User).filter(User.role.in_(["admin", "faculty", "hod"])).all()
    for staff in staff_members:
        db.add(Notification(
            user_id=staff.id,
            title="New Profile Correction Request",
            message=f"Student {current_user.name} has submitted a profile correction request for '{payload.field}'."
        ))
    db.commit()

    return req

@router.get("/correction-requests", response_model=List[CorrectionRequestResponse])
def get_correction_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "student":
        return db.query(CorrectionRequest).filter(CorrectionRequest.student_id == current_user.id).order_by(CorrectionRequest.created_at.desc()).all()
        
    if current_user.role in ["admin", "tnp"]:
        return db.query(CorrectionRequest).order_by(CorrectionRequest.created_at.desc()).all()
        
    if current_user.role in ["faculty", "hod"]:
        permitted_student_ids = get_permitted_student_query(current_user, db, "VIEW").with_entities(Student.id)
        return db.query(CorrectionRequest).filter(CorrectionRequest.student_id.in_(permitted_student_ids)).order_by(CorrectionRequest.created_at.desc()).all()
        
    return []

@router.put("/correction-requests/{request_id}/action")
def action_correction_request(
    request_id: int,
    action_data: CorrectionRequestAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only Admins can process correction requests")

    req = db.query(CorrectionRequest).filter(CorrectionRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Correction request not found")

    if req.status != "Pending":
        raise HTTPException(status_code=400, detail="Request has already been processed")

    req.status = action_data.status

    if action_data.status == "Approved":
        # Apply change to Student record
        field_name = req.field.lower().strip()
        student = req.student
        
        if field_name == "name":
            student.user.name = req.requested_value
        elif field_name == "cgpa":
            student.cgpa = float(req.requested_value)
        elif field_name == "attendance" or field_name == "academic attendance":
            student.attendance = float(req.requested_value)
        elif field_name == "backlogs":
            student.backlogs = int(req.requested_value)
        elif field_name == "section":
            student.section = req.requested_value
        elif field_name in ["batch", "year", "graduation year"]:
            student.batch = req.requested_value
        elif field_name == "email":
            student.user.email = req.requested_value
        elif field_name in ["branch", "department"]:
            dept = db.query(Department).filter(Department.code == req.requested_value.upper()).first()
            if dept:
                student.dept_id = dept.id
            else:
                raise HTTPException(status_code=400, detail=f"Department code '{req.requested_value}' not found")
        
        # Recalculate ML readiness score
        report = predictor.evaluate_student(student, db)
        student.readiness_score = report["readiness_score"]
        student.placement_probability = report["placement_probability"]
        student.ai_recommendations = json.dumps({
            "skills_gap": report["skills_gap"],
            "recommended_skills": report["recommended_skills"],
            "recommended_projects": report["recommended_projects"],
            "recommended_certifications": report["recommended_certifications"],
            "improvement_tips": report["improvement_tips"]
        })

    # Trigger student notification (Req 12)
    from backend.app.models import Notification
    db.add(Notification(
        user_id=req.student_id,
        title="Correction Request Resolved",
        message=f"Your profile correction request for field '{req.field}' has been {action_data.status.lower()} by administrative team."
    ))

    # Log audit
    log = SystemLog(
        user_email=current_user.email,
        action=f"CORRECTION_REQUEST_{action_data.status.upper()}",
        details=f"Processed correction request ID {request_id} for Student ID {req.student_id} - Result: {action_data.status}"
    )
    db.add(log)
    db.commit()
    return {"message": f"Correction request updated to {action_data.status}"}

# STUDENT TIMELINE
@router.get("/timeline")
def get_student_timeline(
    student_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_id = current_user.id
    if current_user.role == "parent":
        parent = db.query(Parent).filter(Parent.id == current_user.id).first()
        if parent:
            target_id = parent.student_id
    elif current_user.role in ["admin", "faculty", "tnp", "hod"] and student_id:
        target_id = student_id
    elif current_user.role == "student":
        target_id = current_user.id

    student = enforce_student_scope(current_user, target_id, db, "VIEW")

    timeline = []
    
    # 1. Activities Attendance
    attendances = db.query(ActivityAttendance).filter(ActivityAttendance.student_id == target_id).all()
    for att in attendances:
        timeline.append({
            "date": att.activity.date.strftime("%Y-%m-%d") if att.activity.date else "Recent",
            "title": f"{att.activity.activity_name} ({att.activity.activity_type})",
            "status": att.status,
            "remarks": att.remarks or "",
            "type": "activity"
        })

    # 2. Applications
    applications = db.query(Application).filter(Application.student_id == target_id).all()
    for app in applications:
        timeline.append({
            "date": app.applied_date.strftime("%Y-%m-%d") if app.applied_date else "Recent",
            "title": f"Applied to {app.drive.company.name} — {app.drive.role}",
            "status": app.status,
            "remarks": app.remarks or "",
            "type": "application"
        })

    # 3. Interviews
    interviews = db.query(Interview).filter(Interview.student_id == target_id).all()
    for iv in interviews:
        timeline.append({
            "date": iv.interview_date.strftime("%Y-%m-%d") if iv.interview_date else "Recent",
            "title": f"Interview Round: {iv.round_name} ({iv.application.drive.company.name})",
            "status": iv.status,
            "remarks": iv.remarks or "",
            "type": "interview"
        })

    # Sort timeline by date
    timeline = sorted(timeline, key=lambda x: x["date"], reverse=True)
    return timeline

@router.get("/{student_id}")
def get_student_by_id(student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = enforce_student_scope(current_user, student_id, db, "VIEW")

    # Parse JSON properties
    try:
        skills = json.loads(student.skills) if student.skills else []
    except:
        skills = student.skills.split(",") if student.skills else []
    
    try:
        projects = json.loads(student.projects) if student.projects else []
    except:
        projects = []

    try:
        certifications = json.loads(student.certifications) if student.certifications else []
    except:
        certifications = []

    try:
        internships = json.loads(student.internships) if student.internships else []
    except:
        internships = []

    try:
        recommendations = json.loads(student.ai_recommendations) if student.ai_recommendations else {}
    except:
        recommendations = {}

    return {
        "id": student.id,
        "name": student.user.name,
        "email": student.user.email,
        "dept_id": student.dept_id,
        "dept_code": student.department.code,
        "dept_name": student.department.name,
        "gender": student.gender,
        "batch": student.batch,
        "phone": student.phone,
        "cgpa": student.cgpa,
        "attendance": student.attendance,
        "backlogs": student.backlogs,
        "sgpa_sem1": student.sgpa_sem1,
        "sgpa_sem2": student.sgpa_sem2,
        "sgpa_sem3": student.sgpa_sem3,
        "sgpa_sem4": student.sgpa_sem4,
        "sgpa_sem5": student.sgpa_sem5,
        "sgpa_sem6": student.sgpa_sem6,
        "sgpa_sem7": student.sgpa_sem7,
        "sgpa_sem8": student.sgpa_sem8,
        "skills": skills,
        "projects": projects,
        "internships": internships,
        "certifications": certifications,
        "github_url": student.github_url,
        "linkedin_url": student.linkedin_url,
        "leetcode_score": student.leetcode_score,
        "codechef_score": student.codechef_score,
        "hackerrank_score": student.hackerrank_score,
        "readiness_score": student.readiness_score,
        "placement_probability": student.placement_probability,
        "ai_recommendations": recommendations,
        "status": student.status,
        "profile_completed": student.profile_completed,
        "verification_status": student.verification_status,
        "section": student.section
    }

@router.put("/{student_id}")
def update_student(student_id: int, student_data: StudentUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "parent":
        raise HTTPException(status_code=403, detail="Access denied: Parents cannot edit student profiles")
    student = enforce_student_scope(current_user, student_id, db, "EDIT")

    # Update student model fields
    update_dict = student_data.model_dump(exclude_unset=True)
    
    # Locked fields validation for verified students
    if current_user.role == "student":
        for administrative_field in [
            "verification_status", "profile_completed", "readiness_score",
            "placement_probability", "status", "ai_recommendations"
        ]:
            update_dict.pop(administrative_field, None)

        if student.verification_status == "VERIFIED" or student.profile_completed:
            locked_fields = ["cgpa", "attendance", "backlogs", "dept_id", "batch", "section", "gender"]
            for field in locked_fields:
                if field in update_dict and update_dict[field] is not None and update_dict[field] != getattr(student, field):
                    raise HTTPException(
                        status_code=403,
                        detail="Academic metrics (CGPA, attendance, backlogs, department, batch, section, gender) cannot be modified on verified or completed profiles. Please submit a correction request."
                    )

    # Handle list serialization for JSON columns
    if "skills" in update_dict and isinstance(update_dict["skills"], list):
        update_dict["skills"] = json.dumps(update_dict["skills"])
    if "projects" in update_dict and isinstance(update_dict["projects"], list):
        update_dict["projects"] = json.dumps(update_dict["projects"])
    if "certifications" in update_dict and isinstance(update_dict["certifications"], list):
        update_dict["certifications"] = json.dumps(update_dict["certifications"])
    if "internships" in update_dict and isinstance(update_dict["internships"], list):
        update_dict["internships"] = json.dumps(update_dict["internships"])

    for key, value in update_dict.items():
        setattr(student, key, value)
    
    student.profile_completed = True
    if current_user.role == "student" and student.verification_status == "UNVERIFIED":
        student.verification_status = "VERIFIED"
    db.commit()

    # Recalculate AI score on modification!
    report = predictor.evaluate_student(student, db)
    student.readiness_score = report["readiness_score"]
    student.placement_probability = report["placement_probability"]
    student.ai_recommendations = json.dumps({
        "skills_gap": report["skills_gap"],
        "recommended_skills": report["recommended_skills"],
        "recommended_projects": report["recommended_projects"],
        "recommended_certifications": report["recommended_certifications"],
        "improvement_tips": report["improvement_tips"]
    })
    
    if student.batch == "2026" and student.status != "Placed":
        student.status = "At Risk" if report["at_risk"] else "Unplaced"
        
    db.commit()
    db.refresh(student)

    # Trigger low attendance notifications (Req 12)
    if student.attendance < 75.0:
        from backend.app.models import Notification
        db.add(Notification(
            user_id=student.id,
            title="Attendance Warning",
            message=f"Warning: Your academic attendance is {student.attendance}%, which is below the required 75% threshold."
        ))
        db.add(Notification(
            user_id=student.id,
            title="[Parent Alert] Academic Attendance Warning",
            message=f"Important: Your ward {student.user.name}'s attendance has dropped to {student.attendance}%, which is below the minimum required 75% for placement eligibility."
        ))
        staff_members = db.query(User).filter(User.role.in_(["faculty", "hod"])).all()
        for staff in staff_members:
            db.add(Notification(
                user_id=staff.id,
                title="Student Attendance Issue",
                message=f"Alert: Student {student.user.name} ({student.id}) has a low attendance of {student.attendance}%."
            ))
        db.commit()

    # Log action
    log = SystemLog(user_email=current_user.email, action="Update Profile", details=f"Student ID {student.id} updated their profile details.")
    db.add(log)
    db.commit()

    return {"message": "Profile updated and AI predictions recalculated successfully!"}

@router.post("/bulk-upload")
def bulk_upload_students(
    payload: List[dict],
    preview: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import student list from bulk JSON structure (handles CSV/Excel parser outputs).
    Supports validation preview (Total, Valid, Duplicates, Invalid) with admin confirmation.
    """
    if current_user.role not in ["faculty", "admin", "hod"]:
        raise HTTPException(status_code=403, detail="Access denied")

    departments = db.query(Department).all()
    dept_map = {d.code.upper(): d.id for d in departments}

    default_pwd_hash = get_password_hash("password123")
    
    # 1. Verification phase
    valid_records = []
    duplicate_records = []
    invalid_records = []
    
    # Pre-fetch existing emails and student IDs to check duplicates
    emails_in_payload = [item.get("email") for item in payload if item.get("email")]
    existing_users = db.query(User).filter(User.email.in_(emails_in_payload)).all()
    existing_emails = {u.email.lower() for u in existing_users}
    
    roll_numbers_in_payload = []
    for item in payload:
        roll = item.get("roll_number") or item.get("id")
        if roll:
            try:
                roll_numbers_in_payload.append(int(roll))
            except ValueError:
                pass
                
    existing_students = db.query(Student).filter(Student.id.in_(roll_numbers_in_payload)).all()
    existing_rolls = {s.id for s in existing_students}

    seen_emails_in_batch = set()
    seen_rolls_in_batch = set()

    for idx, item in enumerate(payload):
        row_num = idx + 1
        email = item.get("email")
        name = item.get("name")
        dept_code = str(item.get("department", "CSE")).upper()
        
        roll_val = item.get("roll_number") or item.get("id")
        roll_num = None
        if roll_val:
            try:
                roll_num = int(roll_val)
            except ValueError:
                pass
                
        # Validate fields
        reasons = []
        if not email:
            reasons.append("Email is missing")
        elif "@" not in email:
            reasons.append("Invalid email format")
            
        if not name:
            reasons.append("Name is missing")
            
        if dept_code not in dept_map:
            reasons.append(f"Department code '{dept_code}' not found in database")
            
        try:
            cgpa = float(item.get("cgpa", 7.0))
            if cgpa < 0.0 or cgpa > 10.0:
                reasons.append(f"CGPA ({cgpa}) must be between 0.0 and 10.0")
        except (ValueError, TypeError):
            reasons.append("CGPA must be a decimal number")
            
        try:
            attendance = float(item.get("attendance", 80.0))
            if attendance < 0.0 or attendance > 100.0:
                reasons.append(f"Attendance ({attendance}) must be between 0.0 and 100.0")
        except (ValueError, TypeError):
            reasons.append("Attendance must be a decimal number")
            
        try:
            backlogs = int(item.get("backlogs", 0))
            if backlogs < 0:
                reasons.append("Backlogs cannot be negative")
        except (ValueError, TypeError):
            reasons.append("Backlogs must be an integer")

        # Determine Status
        if reasons:
            status_str = "Invalid"
            reason_str = ", ".join(reasons)
            invalid_records.append({
                "row": row_num,
                "roll_number": roll_val or "Auto-Generated",
                "name": name or "Unknown",
                "branch": dept_code,
                "status": status_str,
                "reason": reason_str,
                "item": item
            })
        else:
            # Check duplicate in DB or within batch
            is_dup = False
            dup_reasons = []
            
            if email and email.lower() in existing_emails:
                is_dup = True
                dup_reasons.append(f"Email '{email}' already exists in database")
            if email and email.lower() in seen_emails_in_batch:
                is_dup = True
                dup_reasons.append(f"Duplicate email '{email}' in batch")
                
            if roll_num and roll_num in existing_rolls:
                is_dup = True
                dup_reasons.append(f"Roll Number '{roll_num}' already exists in database")
            if roll_num and roll_num in seen_rolls_in_batch:
                is_dup = True
                dup_reasons.append(f"Duplicate Roll Number '{roll_num}' in batch")
                
            if is_dup:
                status_str = "Duplicate"
                reason_str = ", ".join(dup_reasons)
                duplicate_records.append({
                    "row": row_num,
                    "roll_number": roll_val or "Auto-Generated",
                    "name": name,
                    "branch": dept_code,
                    "status": status_str,
                    "reason": reason_str,
                    "item": item
                })
            else:
                if email:
                    seen_emails_in_batch.add(email.lower())
                if roll_num:
                    seen_rolls_in_batch.add(roll_num)
                valid_records.append({
                    "row": row_num,
                    "roll_number": roll_val or "Auto-Generated",
                    "name": name,
                    "branch": dept_code,
                    "status": "Valid",
                    "reason": "OK",
                    "item": item
                })

    if preview:
        return {
            "preview": True,
            "total": len(payload),
            "valid": len(valid_records),
            "duplicates": len(duplicate_records),
            "invalid": len(invalid_records),
            "records": valid_records + duplicate_records + invalid_records
        }

    # 2. Database Commit Phase (Only if preview=False)
    count = 0
    for vr in valid_records:
        item = vr["item"]
        email = item.get("email")
        name = item.get("name")
        dept_code = str(item.get("department", "CSE")).upper()
        dept_id = dept_map.get(dept_code, 1)
        gender = item.get("gender", "Male")
        batch = str(item.get("batch", "2026"))
        cgpa = float(item.get("cgpa", 7.0))
        attendance = float(item.get("attendance", 80.0))
        backlogs = int(item.get("backlogs", 0))

        # Create User
        u_record = User(
            email=email,
            password_hash=default_pwd_hash,
            name=name,
            role="student"
        )
        db.add(u_record)
        db.commit() # Commit to generate ID

        # Prepare Student record
        student = Student(
            id=u_record.id,
            dept_id=dept_id,
            gender=gender,
            batch=batch,
            phone=str(item.get("phone", "9876543210")),
            cgpa=cgpa,
            attendance=attendance,
            backlogs=backlogs,
            skills=json.dumps(item.get("skills", ["SQL", "Java"])),
            projects=json.dumps([]),
            certifications=json.dumps([]),
            status="Unplaced" if cgpa >= 6.0 else "At Risk"
        )
        db.add(student)
        count += 1

    db.commit()

    if count > 0:
        # Retrain ML Predictor to incorporate new students
        print("Retraining ML Predictor with new bulk data...")
        predictor.train_model(db)

        # Re-evaluate all students in the database
        all_students = db.query(Student).all()
        for student in all_students:
            report = predictor.evaluate_student(student, db)
            student.readiness_score = report["readiness_score"]
            student.placement_probability = report["placement_probability"]
            student.ai_recommendations = json.dumps({
                "skills_gap": report["skills_gap"],
                "recommended_skills": report["recommended_skills"],
                "recommended_projects": report["recommended_projects"],
                "recommended_certifications": report["recommended_certifications"],
                "improvement_tips": report["improvement_tips"]
            })
            if student.batch == "2026" and student.status != "Placed":
                student.status = "At Risk" if report["at_risk"] else "Unplaced"
        db.commit()

        log = SystemLog(user_email=current_user.email, action="Bulk Upload", details=f"Bulk imported {count} student records and retrained ML predictor.")
        db.add(log)
        db.commit()

    return {"message": f"Successfully imported {count} students. Machine Learning models updated."}

from pydantic import BaseModel

class StudentRegisterRequest(BaseModel):
    name: str
    email: str
    password: Optional[str] = "password123"
    dept_id: int
    gender: str
    batch: str
    phone: Optional[str] = "9876543210"
    cgpa: float
    attendance: float
    backlogs: int = 0
    skills: Optional[str] = "[]"

@router.post("")
def create_student(
    payload: StudentRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["faculty", "admin", "hod"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if email exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    pwd_hash = get_password_hash(payload.password)
    user_rec = User(
        email=payload.email,
        password_hash=pwd_hash,
        name=payload.name,
        role="student"
    )
    db.add(user_rec)
    db.commit()
    
    student_rec = Student(
        id=user_rec.id,
        dept_id=payload.dept_id,
        gender=payload.gender,
        batch=payload.batch,
        phone=payload.phone,
        cgpa=payload.cgpa,
        attendance=payload.attendance,
        backlogs=payload.backlogs,
        skills=payload.skills if payload.skills else json.dumps(["SQL", "Java"]),
        projects=json.dumps([]),
        certifications=json.dumps([]),
        status="Unplaced" if payload.cgpa >= 6.0 else "At Risk"
    )
    db.add(student_rec)
    db.commit()
    
    # Evaluate AI
    report = predictor.evaluate_student(student_rec, db)
    student_rec.readiness_score = report["readiness_score"]
    student_rec.placement_probability = report["placement_probability"]
    student_rec.ai_recommendations = json.dumps({
        "skills_gap": report["skills_gap"],
        "recommended_skills": report["recommended_skills"],
        "recommended_projects": report["recommended_projects"],
        "recommended_certifications": report["recommended_certifications"],
        "improvement_tips": report["improvement_tips"]
    })
    db.commit()
    
    # Log
    log = SystemLog(user_email=current_user.email, action="Create Student", details=f"Registered student {payload.name} (ID: {user_rec.id}).")
    db.add(log)
    db.commit()
    
    return {"message": "Student created and evaluated successfully!", "student_id": user_rec.id}

@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["faculty", "admin", "hod"]:
        raise HTTPException(status_code=403, detail="Access denied")
        
    student = enforce_student_scope(current_user, student_id, db, "DELETE")
    user_rec = db.query(User).filter(User.id == student_id).first()
    
    # Delete student and user
    db.delete(student)
    if user_rec:
        db.delete(user_rec)
    db.commit()
    
    # Log
    log = SystemLog(user_email=current_user.email, action="Delete Student", details=f"Deleted student ID {student_id}.")
    db.add(log)
    db.commit()
    
    return {"message": "Student deleted successfully"}



# STUDENT 360 DEGREE VIEW
@router.get("/360/{student_id}")
def get_student_360(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "faculty", "tnp", "hod", "parent"]:
        raise HTTPException(status_code=403, detail="Access denied")

    student = enforce_student_scope(current_user, student_id, db, "VIEW")

    # Fetch Profile info
    profile = get_student_by_id(student_id=student_id, current_user=current_user, db=db)
    
    # Fetch Applications
    apps = db.query(Application).filter(Application.student_id == student_id).all()
    apps_list = [{
        "company_name": app.drive.company.name if (app.drive and app.drive.company) else "Unknown Company",
        "role": app.drive.role if app.drive else "N/A",
        "package_lpa": app.drive.package_lpa if app.drive else 0.0,
        "status": app.status,
        "current_round": app.current_round,
        "applied_date": app.applied_date
    } for app in apps]

    # Fetch Interviews
    interviews = db.query(Interview).filter(Interview.student_id == student_id).all()
    interviews_list = [{
        "company_name": iv.application.drive.company.name if (iv.application and iv.application.drive and iv.application.drive.company) else "Unknown Company",
        "round_name": iv.round_name,
        "status": iv.status,
        "interview_date": iv.interview_date
    } for iv in interviews]

    # Fetch Activity Attendance
    from backend.app.models import ActivityAttendance
    activity_att = db.query(ActivityAttendance).filter(ActivityAttendance.student_id == student_id).all()
    activities_list = [{
        "activity_name": att.activity.activity_name if att.activity else "Unknown Activity",
        "activity_type": att.activity.activity_type if att.activity else "N/A",
        "date": att.activity.date if att.activity else None,
        "status": att.status,
        "remarks": att.remarks
    } for att in activity_att]

    # Fetch Feedbacks
    from backend.app.models import Feedback
    feedbacks = db.query(Feedback).join(Interview).filter(Interview.student_id == student_id).all()
    feedbacks_list = [{
        "company_name": fb.interview.application.drive.company.name if (fb.interview and fb.interview.application and fb.interview.application.drive and fb.interview.application.drive.company) else "Unknown Company",
        "experience_text": fb.experience_text,
        "difficulty_rating": fb.difficulty_rating,
        "sentiment_score": fb.sentiment_score
    } for fb in feedbacks]

    # Fetch Placement Eligibility (Req 8 & 11)
    from backend.app.models import PlacementDrive
    drives = db.query(PlacementDrive).all()
    eligibility_list = []
    for drive in drives:
        status_res = predictor.smart_eligibility_check(student, drive)
        eligibility_list.append({
            "drive_id": drive.id,
            "company_name": drive.company.name if drive.company else "Unknown Company",
            "role": drive.role,
            "is_eligible": status_res["is_eligible"],
            "reasons": status_res["reasons"]
        })

    # Timeline
    timeline = get_student_timeline(student_id=student_id, current_user=current_user, db=db)

    return {
        "profile": profile,
        "applications": apps_list,
        "interviews": interviews_list,
        "activity_attendance": activities_list,
        "feedbacks": feedbacks_list,
        "timeline": timeline,
        "eligibility": eligibility_list
    }
