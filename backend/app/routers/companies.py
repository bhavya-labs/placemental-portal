from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import date
from backend.app.database import get_db
from backend.app.models import User, Company, PlacementDrive, Student, Application, Department, SystemLog
from backend.app.schemas import CompanyCreate, PlacementDriveCreate, PlacementDriveUpdateResponse
from backend.app.auth import get_current_user, verify_permission, get_permitted_student_query

router = APIRouter(prefix="", tags=["Companies & Drives"])

@router.get("/api/companies")
def get_companies(
    page: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve companies with optional explicit limit/offset/page pagination and search filtering.
    """
    query = db.query(Company)
    if search:
        query = query.filter(Company.name.ilike(f"%{search}%"))
    query = query.order_by(Company.name)

    if limit is not None or page is not None or offset is not None:
        safe_limit = min(max(limit if limit is not None else 20, 1), 100)
        actual_offset = offset if (offset is not None and offset >= 0) else (max(page if page else 1, 1) - 1) * safe_limit
        return query.offset(actual_offset).limit(safe_limit).all()

    return query.all()

@router.post("/api/companies")
def create_company(company_data: CompanyCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_permission(current_user, "Placement Drives", "CREATE", db)
    
    # Check if duplicate
    existing = db.query(Company).filter(Company.name == company_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company name already exists")
        
    company = Company(**company_data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

# PUBLIC DRIVES (NO AUTH REQUIRED)
@router.get("/api/public/active-drives")
def get_public_active_drives(db: Session = Depends(get_db)):
    """
    Publicly accessible endpoint returning non-sensitive placement drive information
    for active/published drives, intended for prospective viewers on the landing page.
    Requires no authentication.
    """
    drives = (
        db.query(PlacementDrive)
        .join(Company)
        .filter(PlacementDrive.status.in_(["PUBLISHED", "REGISTRATION_OPEN", "Active"]))
        .order_by(PlacementDrive.deadline.asc(), PlacementDrive.interview_date.asc())
        .all()
    )
    return [
        {
            "id": d.id,
            "company_name": d.company.name,
            "role": d.role,
            "package_lpa": d.package_lpa,
            "location": d.location,
            "cgpa_cutoff": d.cgpa_cutoff,
            "deadline": str(d.deadline) if d.deadline else None,
            "company_logo": d.company_logo,
            "job_type": d.job_type,
            "work_mode": d.work_mode,
            "status": d.status
        }
        for d in drives
    ]

# DRIVES

def check_student_drive_eligibility(student_profile: Student, drive: PlacementDrive) -> bool:
    dept_code = student_profile.department.code.upper() if student_profile.department else ""
    allowed_depts = [dept.strip().upper() for dept in (drive.allowed_depts or "").split(",")]
    is_dept_ok = "ALL" in allowed_depts or dept_code in allowed_depts
    is_batch_ok = not drive.batch or drive.batch == student_profile.batch
    is_cgpa_ok = student_profile.cgpa >= (drive.cgpa_cutoff or 0.0)
    is_backlogs_ok = student_profile.backlogs <= (drive.allowed_backlogs if drive.allowed_backlogs is not None else 999)
    is_attendance_ok = student_profile.attendance >= (drive.min_attendance or 0.0)
    return is_dept_ok and is_batch_ok and is_cgpa_ok and is_backlogs_ok and is_attendance_ok

@router.get("/api/drives")
def get_drives(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(PlacementDrive).join(Company)
    if status_filter:
        if status_filter.upper() == "ACTIVE":
            query = query.filter(PlacementDrive.status.in_(["REGISTRATION_OPEN", "PUBLISHED"]))
        else:
            query = query.filter(PlacementDrive.status == status_filter)
    
    results = query.order_by(PlacementDrive.interview_date).all()
    
    if current_user.role == "student":
        student_profile = db.query(Student).filter(Student.id == current_user.id).first()
        if student_profile:
            applied_drive_ids = {a.drive_id for a in db.query(Application.drive_id).filter(Application.student_id == student_profile.id).all()}
            filtered_results = []
            for d in results:
                # Always show drives the student has actively applied to
                if d.id in applied_drive_ids or check_student_drive_eligibility(student_profile, d):
                    filtered_results.append(d)
            results = filtered_results
    
    drives_list = []
    for d in results:
        drives_list.append({
            "id": d.id,
            "company_id": d.company_id,
            "company_name": d.company.name,
            "role": d.role,
            "package_lpa": d.package_lpa,
            "location": d.location,
            "cgpa_cutoff": d.cgpa_cutoff,
            "allowed_depts": d.allowed_depts,
            "allowed_backlogs": d.allowed_backlogs,
            "bond_details": d.bond_details,
            "selection_process": d.selection_process,
            "interview_date": d.interview_date,
            "deadline": d.deadline,
            "status": d.status,
            "job_id": d.job_id,
            "batch": d.batch,
            "min_attendance": d.min_attendance,
            "responsibilities": d.responsibilities,
            "required_skills": d.required_skills,
            "preferred_skills": d.preferred_skills,
            "job_type": d.job_type,
            "work_mode": d.work_mode,
            "openings_count": d.openings_count,
            "hiring_process": d.hiring_process,
            "jd_pdf_path": d.jd_pdf_path,
            "company_logo": d.company_logo
        })
    return drives_list

@router.post("/api/drives")
def create_drive(drive_data: PlacementDriveCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_permission(current_user, "Placement Drives", "CREATE", db)
    
    company_id = drive_data.company_id
    if company_id:
        existing_comp = db.query(Company).filter(Company.id == company_id).first()
        if not existing_comp:
            raise HTTPException(status_code=400, detail="Referenced company does not exist")
    elif drive_data.company_name:
        comp = db.query(Company).filter(Company.name.ilike(drive_data.company_name.strip())).first()
        if not comp:
            comp = Company(
                name=drive_data.company_name.strip(),
                industry="Technology",
                website="https://example.com",
                description="Auto-registered company"
            )
            db.add(comp)
            db.commit()
            db.refresh(comp)
        company_id = comp.id
        
    if not company_id:
        raise HTTPException(status_code=400, detail="Either company_id or company_name must be provided")
        
    drive_dict = drive_data.model_dump()
    drive_dict["company_id"] = company_id
    drive_dict.pop("company_name", None)
        
    drive = PlacementDrive(**drive_dict)
    db.add(drive)
    db.commit()
    db.refresh(drive)

    # Audit Logging (Req 13)
    log = SystemLog(
        user_email=current_user.email,
        action="CREATE_PLACEMENT_DRIVE",
        details=f"Created drive ID {drive.id} for Company ID {drive.company_id} ({drive.role}, batch: {drive.batch}, min_attendance: {drive.min_attendance}%)."
    )
    db.add(log)
    db.commit()

    # Trigger published notifications (Req 12)
    if drive.status == "PUBLISHED":
        from backend.app.models import Notification
        students = db.query(Student).all()
        for s in students:
            notif = Notification(
                user_id=s.id,
                title="New Placement Drive Published",
                message=f"{drive.company.name} is hiring for the role '{drive.role}'. Package: {drive.package_lpa} LPA. Apply before {drive.deadline.strftime('%Y-%m-%d')}."
            )
            db.add(notif)
        db.commit()

    return {
        "id": drive.id,
        "company_id": drive.company_id,
        "role": drive.role,
        "package_lpa": drive.package_lpa,
        "location": drive.location,
        "cgpa_cutoff": drive.cgpa_cutoff,
        "allowed_depts": drive.allowed_depts,
        "allowed_backlogs": drive.allowed_backlogs,
        "bond_details": drive.bond_details,
        "selection_process": drive.selection_process,
        "interview_date": drive.interview_date,
        "deadline": drive.deadline,
        "status": drive.status,
        "job_id": drive.job_id,
        "batch": drive.batch,
        "min_attendance": drive.min_attendance
    }

@router.get("/api/drives/{drive_id}")
def get_drive_details(drive_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    drive = db.query(PlacementDrive).filter(PlacementDrive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Placement drive not found")

    # Enforce student eligibility check
    if current_user.role == "student":
        student_profile = db.query(Student).filter(Student.id == current_user.id).first()
        if not student_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

        has_applied = db.query(Application).filter(
            Application.student_id == student_profile.id,
            Application.drive_id == drive.id
        ).first() is not None

        if not has_applied and not check_student_drive_eligibility(student_profile, drive):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not meet the eligibility criteria for this placement drive"
            )

    # Fetch applied students count (filtered by user's permitted student scope)
    applied_list = []
    try:
        permitted_student_ids = get_permitted_student_query(current_user, db, "VIEW").with_entities(Student.id)
        applications = db.query(Application).filter(
            Application.drive_id == drive_id,
            Application.student_id.in_(permitted_student_ids)
        ).all()
    except HTTPException:
        applications = []
    
    for app in applications:
        student = app.student
        applied_list.append({
            "application_id": app.id,
            "student_id": student.id,
            "name": student.user.name,
            "email": student.user.email,
            "dept_code": student.department.code,
            "cgpa": student.cgpa,
            "status": app.status,
            "current_round": app.current_round,
            "joining_status": app.joining_status,
            "applied_date": app.applied_date
        })

    # Fetch eligible students counts
    allowed_depts = [dept.strip().upper() for dept in drive.allowed_depts.split(",")]
    
    eligible_students_query = db.query(Student).filter(
        Student.cgpa >= drive.cgpa_cutoff,
        Student.backlogs <= drive.allowed_backlogs,
        Student.batch == "2026"
    )
    
    # Department filter
    if "ALL" not in allowed_depts:
        eligible_students_query = eligible_students_query.join(Department).filter(
            Department.code.in_(allowed_depts)
        )
        
    eligible_count = eligible_students_query.count()

    return {
        "id": drive.id,
        "company_id": drive.company_id,
        "company_name": drive.company.name,
        "role": drive.role,
        "package_lpa": drive.package_lpa,
        "location": drive.location,
        "cgpa_cutoff": drive.cgpa_cutoff,
        "allowed_depts": drive.allowed_depts,
        "allowed_backlogs": drive.allowed_backlogs,
        "bond_details": drive.bond_details,
        "selection_process": drive.selection_process,
        "interview_date": drive.interview_date,
        "deadline": drive.deadline,
        "status": drive.status,
        "job_id": drive.job_id,
        "batch": drive.batch,
        "min_attendance": drive.min_attendance,
        "responsibilities": drive.responsibilities,
        "required_skills": drive.required_skills,
        "preferred_skills": drive.preferred_skills,
        "job_type": drive.job_type,
        "work_mode": drive.work_mode,
        "openings_count": drive.openings_count,
        "hiring_process": drive.hiring_process,
        "jd_pdf_path": drive.jd_pdf_path,
        "company_logo": drive.company_logo,
        "students_applied": applied_list,
        "applied_list": applied_list,
        "students_eligible_count": eligible_count
    }

@router.get("/api/drives/{drive_id}/eligible-students")
def get_eligible_students_list(drive_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_permission(current_user, "Student Performance", "VIEW", db)

    drive = db.query(PlacementDrive).filter(PlacementDrive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Placement drive not found")

    allowed_depts = [dept.strip().upper() for dept in drive.allowed_depts.split(",")]
    
    # Query batch students who meet CGPA cutoff, backlog, batch, and attendance criteria (Req 8 & 11)
    eligible_query = db.query(Student).filter(
        Student.cgpa >= drive.cgpa_cutoff,
        Student.backlogs <= drive.allowed_backlogs,
        Student.batch == drive.batch,
        Student.attendance >= drive.min_attendance
    )

    if "ALL" not in allowed_depts:
        eligible_query = eligible_query.join(Department).filter(
            Department.code.in_(allowed_depts)
        )

    eligible_students = eligible_query.all()
    results = []
    
    for s in eligible_students:
        results.append({
            "id": s.id,
            "name": s.user.name,
            "email": s.user.email,
            "dept_code": s.department.code,
            "cgpa": s.cgpa,
            "backlogs": s.backlogs,
            "readiness_score": s.readiness_score,
            "phone": s.phone
        })

    return results

@router.put("/api/drives/{drive_id}", response_model=PlacementDriveUpdateResponse)
def update_drive(
    drive_id: int,
    drive_data: PlacementDriveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scope_info = verify_permission(current_user, "Placement Drives", "EDIT", db)
    
    drive = db.query(PlacementDrive).filter(PlacementDrive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Placement drive not found")
        
    # Scope enforcement
    if scope_info.get("scope") == "DEPARTMENT":
        scope_val = str(scope_info.get("scope_value", "")).strip().upper()
        if scope_val.isdigit():
            dept_obj = db.query(Department).filter(Department.id == int(scope_val)).first()
            if dept_obj:
                scope_val = dept_obj.code.upper()
        else:
            dept_by_name = db.query(Department).filter(Department.name.ilike(scope_val)).first()
            if dept_by_name:
                scope_val = dept_by_name.code.upper()
        
        drive_depts = [d.strip().upper() for d in (drive.allowed_depts or "").split(",")]
        if "ALL" not in drive_depts and scope_val not in drive_depts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Placement drive department scope ({drive.allowed_depts}) does not include authorized department ({scope_val})"
            )
        
    company_id = drive_data.company_id or drive.company_id
    if company_id:
        comp = db.query(Company).filter(Company.id == company_id).first()
        if not comp:
            raise HTTPException(status_code=400, detail="Referenced company does not exist")
    elif drive_data.company_name:
        comp = db.query(Company).filter(Company.name.ilike(drive_data.company_name.strip())).first()
        if not comp:
            comp = Company(
                name=drive_data.company_name.strip(),
                industry="Technology",
                website="https://example.com",
                description="Auto-registered company"
            )
            db.add(comp)
            db.commit()
            db.refresh(comp)
        company_id = comp.id
        
    if not company_id:
        raise HTTPException(status_code=400, detail="Either company_id or company_name must be provided")

    # Lifecycle transition checking (Req 15)
    VALID_TRANSITIONS = {
        "DRAFT": ["PUBLISHED", "Active", "REGISTRATION_OPEN"],
        "PUBLISHED": ["REGISTRATION_OPEN", "Active", "REGISTRATION_CLOSED", "COMPLETED"],
        "Active": ["REGISTRATION_OPEN", "REGISTRATION_CLOSED", "ASSESSMENT", "INTERVIEW", "COMPLETED"],
        "REGISTRATION_OPEN": ["REGISTRATION_CLOSED", "Active", "ASSESSMENT", "COMPLETED"],
        "REGISTRATION_CLOSED": ["ASSESSMENT", "INTERVIEW", "Active", "COMPLETED"],
        "ASSESSMENT": ["INTERVIEW", "RESULT_DECLARED", "COMPLETED"],
        "INTERVIEW": ["RESULT_DECLARED", "COMPLETED"],
        "RESULT_DECLARED": ["COMPLETED", "ARCHIVED"],
        "COMPLETED": ["COMPLETED", "ARCHIVED"],
        "ARCHIVED": ["ARCHIVED"]
    }
    old_status = drive.status
    new_status = drive_data.status
    if old_status != new_status:
        allowed_next = VALID_TRANSITIONS.get(old_status, [])
        if new_status not in allowed_next:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid lifecycle status transition from '{old_status}' to '{new_status}'"
            )
            
    # Track changed fields for audit log
    changes = []
    if drive.status != drive_data.status:
        changes.append(f"status: {drive.status} -> {drive_data.status}")
    if drive.cgpa_cutoff != drive_data.cgpa_cutoff:
        changes.append(f"cgpa_cutoff: {drive.cgpa_cutoff} -> {drive_data.cgpa_cutoff}")
    if drive.allowed_backlogs != drive_data.allowed_backlogs:
        changes.append(f"backlogs: {drive.allowed_backlogs} -> {drive_data.allowed_backlogs}")
    if drive.min_attendance != drive_data.min_attendance:
        changes.append(f"min_attendance: {drive.min_attendance} -> {drive_data.min_attendance}")
    if drive.batch != drive_data.batch:
        changes.append(f"batch: {drive.batch} -> {drive_data.batch}")

    drive_dict = drive_data.model_dump()
    drive_dict["company_id"] = company_id
    drive_dict.pop("company_name", None)

    for k, v in drive_dict.items():
        setattr(drive, k, v)
        
    db.commit()
    db.refresh(drive)

    if changes:
        log = SystemLog(
            user_email=current_user.email,
            action="UPDATE_PLACEMENT_DRIVE",
            details=f"Updated drive ID {drive_id} parameters: {', '.join(changes)}"
        )
        db.add(log)
        db.commit()

        # Trigger notifications (Req 12)
        from backend.app.models import Notification
        if old_status != "PUBLISHED" and new_status == "PUBLISHED":
            students = db.query(Student).all()
            for s in students:
                notif = Notification(
                    user_id=s.id,
                    title="New Placement Drive Published",
                    message=f"{drive.company.name} is hiring for the role '{drive.role}'. Package: {drive.package_lpa} LPA. Apply before {drive.deadline.strftime('%Y-%m-%d')}."
                )
                db.add(notif)
            db.commit()

        # Check if criteria fields changed
        criteria_fields = ["cgpa_cutoff", "allowed_backlogs", "min_attendance", "batch"]
        has_criteria_change = any(any(field in c for field in criteria_fields) for c in changes)
        if has_criteria_change:
            students = db.query(Student).all()
            for s in students:
                notif = Notification(
                    user_id=s.id,
                    title="Eligibility Criteria Updated",
                    message=f"The eligibility criteria for the placement drive of {drive.company.name} ({drive.role}) has been updated. Please verify your eligibility status."
                )
                db.add(notif)
            db.commit()

    db.refresh(drive)
    return {
        "id": drive.id,
        "company_id": drive.company_id,
        "company_name": drive.company.name if drive.company else "",
        "role": drive.role,
        "package_lpa": drive.package_lpa,
        "location": drive.location,
        "cgpa_cutoff": drive.cgpa_cutoff,
        "allowed_depts": drive.allowed_depts,
        "allowed_backlogs": drive.allowed_backlogs,
        "bond_details": drive.bond_details,
        "selection_process": drive.selection_process,
        "interview_date": drive.interview_date,
        "deadline": drive.deadline,
        "status": drive.status,
        "lifecycle_status": drive.status,
        "job_id": drive.job_id,
        "batch": drive.batch,
        "min_attendance": drive.min_attendance,
        "responsibilities": drive.responsibilities,
        "required_skills": drive.required_skills,
        "preferred_skills": drive.preferred_skills,
        "job_type": drive.job_type,
        "work_mode": drive.work_mode,
        "openings_count": drive.openings_count,
        "hiring_process": drive.hiring_process,
        "company_logo": drive.company_logo
    }

@router.delete("/api/drives/{drive_id}")
def delete_drive(
    drive_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_permission(current_user, "Placement Drives", "DELETE", db)
        
    drive = db.query(PlacementDrive).filter(PlacementDrive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Placement drive not found")
        
    db.delete(drive)
    db.commit()
    return {"message": "Placement drive deleted successfully"}

@router.delete("/api/companies/{company_id}")
def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_permission(current_user, "Placement Drives", "DELETE", db)
        
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    db.delete(company)
    db.commit()
    return {"message": "Company and associated placement drives deleted successfully"}
