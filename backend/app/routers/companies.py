from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional, Union, Dict, Any
from datetime import date, datetime, timezone, timedelta

# India Standard Time (UTC+05:30) helper for consistent date boundary handling
IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))

def get_ist_date() -> date:
    """Return the current date in India Standard Time (UTC+05:30)."""
    return datetime.now(IST_TIMEZONE).date()

def parse_date_param(val: Optional[Union[date, str]]) -> Optional[date]:
    """Safely parse a date parameter passed as string or date object."""
    if not val:
        return None
    if isinstance(val, date):
        return val
    val_str = str(val).strip()
    if not val_str:
        return None
    try:
        return datetime.strptime(val_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def build_dept_filter(dept_code: str):
    """
    Construct exact boundary matching condition for allowed departments.
    Prevents substring false positives (e.g. 'IT' matching 'CIVIL', or 'CE' matching 'ECE').
    """
    clean = dept_code.strip().upper()
    return or_(
        PlacementDrive.allowed_depts.ilike("ALL"),
        PlacementDrive.allowed_depts.ilike("ALL,%"),
        PlacementDrive.allowed_depts.ilike("ALL, %"),
        PlacementDrive.allowed_depts.ilike("%,ALL"),
        PlacementDrive.allowed_depts.ilike("%, ALL"),
        PlacementDrive.allowed_depts.ilike("%,ALL,%"),
        PlacementDrive.allowed_depts.ilike("%, ALL,%"),
        PlacementDrive.allowed_depts == clean,
        func.trim(PlacementDrive.allowed_depts).ilike(clean),
        PlacementDrive.allowed_depts.ilike(f"{clean},%"),
        PlacementDrive.allowed_depts.ilike(f"{clean}, %"),
        PlacementDrive.allowed_depts.ilike(f"%,{clean}"),
        PlacementDrive.allowed_depts.ilike(f"%, {clean}"),
        PlacementDrive.allowed_depts.ilike(f"%,{clean},%"),
        PlacementDrive.allowed_depts.ilike(f"%, {clean},%"),
        PlacementDrive.allowed_depts.ilike(f"%,{clean}, %"),
        PlacementDrive.allowed_depts.ilike(f"%, {clean}, %"),
    )

# Canonical lifecycle statuses
STATUS_DRAFT = "DRAFT"
STATUS_SCHEDULED = "SCHEDULED"
STATUS_REGISTRATION_OPEN = "REGISTRATION_OPEN"
STATUS_REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
STATUS_ONGOING = "ONGOING"
STATUS_COMPLETED = "COMPLETED"
STATUS_ARCHIVED = "ARCHIVED"

# Status groups for backward compatibility with existing records
ACTIVE_STATUSES = ["REGISTRATION_OPEN", "PUBLISHED", "Active"]
SCHEDULED_STATUSES = ["SCHEDULED", "Upcoming", "UPCOMING"]
ONGOING_STATUSES = ["ONGOING", "ASSESSMENT", "INTERVIEW", "RESULT_DECLARED"]
COMPLETED_STATUSES = ["COMPLETED", "Completed"]
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

def broadcast_drive_notification(
    db: Session,
    drive: PlacementDrive,
    title: str,
    message: str,
    ref_key: str
) -> int:
    """
    Safely broadcast notifications for a placement drive event.
    - Sends notifications ONLY to eligible students via check_student_drive_eligibility.
    - Enforces idempotency via reference_key to prevent duplicate broadcasts.
    - Preserves existing notifications and handles database transactions safely.
    - Returns count of newly inserted notifications.
    """
    from backend.app.models import Notification, Student

    # 1. Identify already-notified users for this specific reference_key
    already_notified = {
        r[0] for r in db.query(Notification.user_id)
        .filter(Notification.reference_key == ref_key)
        .all()
    }

    # If no reference_key records exist (legacy records), check by exact (title, message)
    if not already_notified:
        already_notified = {
            r[0] for r in db.query(Notification.user_id)
            .filter(Notification.title == title, Notification.message == message)
            .all()
        }

    # 2. Query students and filter for eligibility
    all_students = db.query(Student).all()
    newly_notified = 0
    for s in all_students:
        if s.id not in already_notified and check_student_drive_eligibility(s, drive):
            try:
                # Use nested transaction savepoint to safely handle concurrent duplicate attempts
                with db.begin_nested():
                    notif = Notification(
                        user_id=s.id,
                        title=title,
                        message=message,
                        reference_key=ref_key
                    )
                    db.add(notif)
                    db.flush()
                newly_notified += 1
            except Exception:
                # Uniqueness conflict under concurrent request - rolled back to savepoint
                continue

    if newly_notified > 0:
        db.commit()

    return newly_notified

@router.get("/api/drives")
def get_drives(
    status_filter: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    dept: Optional[str] = None,
    location: Optional[str] = None,
    reg_status: Optional[str] = None,
    date_from: Optional[Union[date, str]] = None,
    date_to: Optional[Union[date, str]] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(PlacementDrive).join(Company)
    
    # 1. Lifecycle status filter
    effective_status = status_filter if status_filter is not None else status
    if effective_status and effective_status.strip().upper() != "ALL":
        s_norm = effective_status.strip().upper()
        if s_norm == "ACTIVE":
            query = query.filter(PlacementDrive.status.in_(ACTIVE_STATUSES))
        elif s_norm == "ARCHIVED":
            query = query.filter(PlacementDrive.status == STATUS_ARCHIVED)
        elif s_norm in ["SCHEDULED", "UPCOMING"]:
            query = query.filter(PlacementDrive.status.in_(SCHEDULED_STATUSES))
        elif s_norm in ["ONGOING", "ASSESSMENT", "INTERVIEW"]:
            query = query.filter(PlacementDrive.status.in_(ONGOING_STATUSES))
        elif s_norm == "COMPLETED":
            query = query.filter(PlacementDrive.status.in_(COMPLETED_STATUSES))
        elif s_norm == "DRAFT":
            query = query.filter(PlacementDrive.status == STATUS_DRAFT)
        elif s_norm == "REGISTRATION_CLOSED":
            query = query.filter(PlacementDrive.status == STATUS_REGISTRATION_CLOSED)
        else:
            query = query.filter(PlacementDrive.status.ilike(effective_status))
    else:
        # Default: EXCLUDE archived drives from normal active listings
        query = query.filter(PlacementDrive.status != STATUS_ARCHIVED)

    # 2. Search filter (case-insensitive partial matching on Company.name, PlacementDrive.role, PlacementDrive.job_id)
    if search and search.strip():
        clean_search = search.strip()
        query = query.filter(
            or_(
                Company.name.ilike(f"%{clean_search}%"),
                PlacementDrive.role.ilike(f"%{clean_search}%"),
                PlacementDrive.job_id.ilike(f"%{clean_search}%")
            )
        )

    # 3. Department filter (target department eligibility matching allowed_depts)
    if dept and dept.strip() and dept.strip().upper() != "ALL":
        query = query.filter(build_dept_filter(dept.strip()))

    # 4. Location filter (case-insensitive partial matching)
    if location and location.strip():
        query = query.filter(PlacementDrive.location.ilike(f"%{location.strip()}%"))

    # 5. Registration status filter (OPEN vs CLOSED based on deadline & IST date)
    today_ist = get_ist_date()
    if reg_status and reg_status.strip():
        norm_reg = reg_status.strip().upper()
        if norm_reg in ["OPEN", "REGISTRATION_OPEN"]:
            query = query.filter(
                PlacementDrive.status.in_(ACTIVE_STATUSES),
                PlacementDrive.deadline >= today_ist
            )
        elif norm_reg in ["CLOSED", "REGISTRATION_CLOSED"]:
            query = query.filter(
                or_(
                    PlacementDrive.status == STATUS_REGISTRATION_CLOSED,
                    and_(
                        PlacementDrive.status.in_(ACTIVE_STATUSES),
                        PlacementDrive.deadline < today_ist
                    )
                )
            )

    # 6. Date range filters on interview_date
    parsed_date_from = parse_date_param(date_from)
    if parsed_date_from:
        query = query.filter(PlacementDrive.interview_date >= parsed_date_from)
    parsed_date_to = parse_date_param(date_to)
    if parsed_date_to:
        query = query.filter(PlacementDrive.interview_date <= parsed_date_to)

    # 7. Department-level RBAC for faculty / HOD users
    if current_user.role in ["faculty", "hod"]:
        try:
            scope_info = verify_permission(current_user, "Placement Drives", "VIEW", db)
            faculty_scope = scope_info.get("scope")
            faculty_scope_value = scope_info.get("scope_value")
        except HTTPException:
            faculty_scope = "NONE"
            faculty_scope_value = None

        if faculty_scope == "ALL":
            pass
        elif faculty_scope == "DEPARTMENT":
            scope_code = str(faculty_scope_value).upper() if faculty_scope_value else ""
            if scope_code.isdigit():
                d_obj = db.query(Department).filter(Department.id == int(scope_code)).first()
                if d_obj:
                    scope_code = d_obj.code.upper()
            if scope_code:
                query = query.filter(build_dept_filter(scope_code))
            else:
                query = query.filter(False)
        elif faculty_scope == "SECTION":
            f_profile = current_user.faculty_profile
            if f_profile and f_profile.department:
                f_dept_code = f_profile.department.code.upper()
                query = query.filter(build_dept_filter(f_dept_code))
            else:
                query = query.filter(False)
        else:
            query = query.filter(False)

    # 8. Pagination bounds and clamping
    is_paginated = (page is not None) or (page_size is not None) or (limit is not None)
    safe_page = max(1, page if page is not None else 1)
    effective_size = page_size if page_size is not None else (limit if limit is not None else 10)
    safe_limit = max(1, min(100, effective_size))
    offset = (safe_page - 1) * safe_limit

    # Student-specific restrictions:
    # 1. Never show DRAFT drives to students
    # 2. Never show ARCHIVED drives as active opportunities
    if current_user.role == "student":
        query = query.filter(PlacementDrive.status.notin_([STATUS_DRAFT, STATUS_ARCHIVED]))
        student_profile = db.query(Student).filter(Student.id == current_user.id).first()
        if student_profile:
            applied_drive_ids = {a.drive_id for a in db.query(Application.drive_id).filter(Application.student_id == student_profile.id).all()}
            raw_results = query.order_by(PlacementDrive.interview_date).all()
            filtered_results = [
                d for d in raw_results
                if d.id in applied_drive_ids or check_student_drive_eligibility(student_profile, d)
            ]
            total_count = len(filtered_results)
            if is_paginated:
                results = filtered_results[offset : offset + safe_limit]
            else:
                results = filtered_results
        else:
            total_count = 0
            results = []
    else:
        total_count = query.count()
        if is_paginated:
            results = query.order_by(PlacementDrive.interview_date).offset(offset).limit(safe_limit).all()
        else:
            results = query.order_by(PlacementDrive.interview_date).all()

    total_pages = max(1, (total_count + safe_limit - 1) // safe_limit) if total_count > 0 else 0

    drives_list = []
    for d in results:
        # Treat drives with no deadline as having registration permanently open (admin/data-entry gap)
        is_reg_open = d.status in ACTIVE_STATUSES and (d.deadline is None or d.deadline >= today_ist)
        is_reg_expired = d.status in ACTIVE_STATUSES and d.deadline is not None and d.deadline < today_ist
        effective_status_val = d.status
        if is_reg_expired:
            effective_status_val = "REGISTRATION_CLOSED"
        elif d.status in SCHEDULED_STATUSES:
            effective_status_val = "SCHEDULED"
        elif d.status in ACTIVE_STATUSES:
            effective_status_val = "REGISTRATION_OPEN"
        elif d.status in ONGOING_STATUSES:
            effective_status_val = "ONGOING"
        elif d.status in COMPLETED_STATUSES:
            effective_status_val = "COMPLETED"
        elif d.status == STATUS_ARCHIVED:
            effective_status_val = "ARCHIVED"
        elif d.status == STATUS_DRAFT:
            effective_status_val = "DRAFT"

        drives_list.append({
            "id": d.id,
            "company_id": d.company_id,
            "company_name": d.company.name if d.company else "",
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
            "effective_status": effective_status_val,
            "is_registration_open": is_reg_open,
            "is_archived": d.status == STATUS_ARCHIVED,
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

    if is_paginated:
        return {
            "items": drives_list,
            "total": total_count,
            "page": safe_page,
            "page_size": safe_limit,
            "total_pages": total_pages
        }
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
    drive_dict.pop("effective_status", None)
    drive_dict.pop("is_registration_open", None)
    drive_dict.pop("is_archived", None)
        
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

    # Trigger published notifications idempotently to eligible students
    if drive.status == "PUBLISHED":
        company_name = drive.company.name if drive.company else "A company"
        deadline_str = drive.deadline.strftime('%Y-%m-%d') if drive.deadline else "the deadline"
        msg = f"{company_name} is hiring for the role '{drive.role}'. Package: {drive.package_lpa} LPA. Apply before {deadline_str}."
        ref_key = f"drive:{drive.id}:published"
        broadcast_drive_notification(db, drive, "New Placement Drive Published", msg, ref_key)

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

    # Enforce student eligibility check and lifecycle visibility
    if current_user.role == "student":
        student_profile = db.query(Student).filter(Student.id == current_user.id).first()
        if not student_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

        has_applied = db.query(Application).filter(
            Application.student_id == student_profile.id,
            Application.drive_id == drive.id
        ).first() is not None

        # Students cannot inspect DRAFT drives, or ARCHIVED drives unless they have an existing application
        if drive.status == STATUS_DRAFT or (drive.status == STATUS_ARCHIVED and not has_applied):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Placement drive not found"
            )

        if not has_applied and not check_student_drive_eligibility(student_profile, drive):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not meet the eligibility criteria for this placement drive"
            )

    # Enforce Faculty / HOD department scoping
    if current_user.role in ["faculty", "hod"]:
        try:
            scope_info = verify_permission(current_user, "Placement Drives", "VIEW", db)
            faculty_scope = scope_info.get("scope")
            faculty_scope_value = scope_info.get("scope_value")
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: No active permission to view placement drives"
            )

        if faculty_scope != "ALL":
            target_dept_code = None
            if faculty_scope == "DEPARTMENT":
                scope_code = str(faculty_scope_value).upper() if faculty_scope_value else ""
                if scope_code.isdigit():
                    d_obj = db.query(Department).filter(Department.id == int(scope_code)).first()
                    if d_obj:
                        target_dept_code = d_obj.code.upper()
                else:
                    target_dept_code = scope_code
            elif faculty_scope == "SECTION":
                if current_user.faculty_profile and current_user.faculty_profile.department:
                    target_dept_code = current_user.faculty_profile.department.code.upper()

            if target_dept_code:
                allowed_depts = [d.strip().upper() for d in (drive.allowed_depts or "").split(",") if d.strip()]
                if "ALL" not in allowed_depts and target_dept_code not in allowed_depts:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Placement drive outside authorized department scope"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Placement drive outside authorized department scope"
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

    today_ist = get_ist_date()
    is_reg_open = drive.status in ACTIVE_STATUSES and drive.deadline >= today_ist
    is_reg_expired = drive.status in ACTIVE_STATUSES and drive.deadline < today_ist
    effective_status = drive.status
    if is_reg_expired:
        effective_status = "REGISTRATION_CLOSED"
    elif drive.status in SCHEDULED_STATUSES:
        effective_status = "SCHEDULED"
    elif drive.status in ACTIVE_STATUSES:
        effective_status = "REGISTRATION_OPEN"
    elif drive.status in ONGOING_STATUSES:
        effective_status = "ONGOING"
    elif drive.status in COMPLETED_STATUSES:
        effective_status = "COMPLETED"
    elif drive.status == STATUS_ARCHIVED:
        effective_status = "ARCHIVED"
    elif drive.status == STATUS_DRAFT:
        effective_status = "DRAFT"

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
        "effective_status": effective_status,
        "is_registration_open": is_reg_open,
        "is_archived": drive.status == STATUS_ARCHIVED,
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

    # Lifecycle transition checking (Req 15 & Batch 2)
    VALID_TRANSITIONS = {
        "DRAFT": ["SCHEDULED", "Upcoming", "UPCOMING", "REGISTRATION_OPEN", "PUBLISHED", "Active", "ARCHIVED"],
        "SCHEDULED": ["REGISTRATION_OPEN", "PUBLISHED", "Active", "REGISTRATION_CLOSED", "DRAFT", "ARCHIVED"],
        "Upcoming": ["REGISTRATION_OPEN", "PUBLISHED", "Active", "REGISTRATION_CLOSED", "DRAFT", "ARCHIVED"],
        "UPCOMING": ["REGISTRATION_OPEN", "PUBLISHED", "Active", "REGISTRATION_CLOSED", "DRAFT", "ARCHIVED"],
        "PUBLISHED": ["REGISTRATION_OPEN", "Active", "REGISTRATION_CLOSED", "ONGOING", "ASSESSMENT", "INTERVIEW", "COMPLETED", "ARCHIVED"],
        "Active": ["REGISTRATION_OPEN", "REGISTRATION_CLOSED", "ONGOING", "ASSESSMENT", "INTERVIEW", "COMPLETED", "ARCHIVED"],
        "REGISTRATION_OPEN": ["REGISTRATION_CLOSED", "Active", "ONGOING", "ASSESSMENT", "INTERVIEW", "COMPLETED", "ARCHIVED"],
        "REGISTRATION_CLOSED": ["REGISTRATION_OPEN", "Active", "ONGOING", "ASSESSMENT", "INTERVIEW", "COMPLETED", "ARCHIVED"],
        "ONGOING": ["REGISTRATION_CLOSED", "ASSESSMENT", "INTERVIEW", "RESULT_DECLARED", "COMPLETED", "ARCHIVED"],
        "ASSESSMENT": ["INTERVIEW", "RESULT_DECLARED", "COMPLETED", "ARCHIVED"],
        "INTERVIEW": ["RESULT_DECLARED", "COMPLETED", "ARCHIVED"],
        "RESULT_DECLARED": ["COMPLETED", "ARCHIVED"],
        "COMPLETED": ["COMPLETED", "ARCHIVED"],
        "Completed": ["Completed", "ARCHIVED"],
        "ARCHIVED": ["ARCHIVED", "DRAFT", "REGISTRATION_OPEN", "COMPLETED"]
    }
    old_status = drive.status
    new_status = drive_data.status
    if old_status != new_status:
        allowed_next = VALID_TRANSITIONS.get(old_status, [])
        if new_status not in allowed_next and new_status != "ARCHIVED":
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
    drive_dict.pop("effective_status", None)
    drive_dict.pop("is_registration_open", None)
    drive_dict.pop("is_archived", None)

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

        # Trigger published notifications idempotently (Req 12)
        if old_status != "PUBLISHED" and new_status == "PUBLISHED":
            company_name = drive.company.name if drive.company else "A company"
            deadline_str = drive.deadline.strftime('%Y-%m-%d') if drive.deadline else "the deadline"
            msg = f"{company_name} is hiring for the role '{drive.role}'. Package: {drive.package_lpa} LPA. Apply before {deadline_str}."
            ref_key = f"drive:{drive.id}:published"
            broadcast_drive_notification(db, drive, "New Placement Drive Published", msg, ref_key)

        # Check if criteria fields changed
        criteria_fields = ["cgpa_cutoff", "allowed_backlogs", "min_attendance", "batch", "allowed_depts"]
        has_criteria_change = any(any(field in c for field in criteria_fields) for c in changes)
        if has_criteria_change and drive.status == "PUBLISHED":
            criteria_sig = f"{drive.cgpa_cutoff}:{drive.allowed_backlogs}:{drive.min_attendance}:{drive.batch}:{drive.allowed_depts}"
            ref_key = f"drive:{drive.id}:criteria:{criteria_sig}"
            company_name = drive.company.name if drive.company else "Company"
            msg = f"The eligibility criteria for the placement drive of {company_name} ({drive.role}) has been updated. Please verify your eligibility status."
            broadcast_drive_notification(db, drive, "Eligibility Criteria Updated", msg, ref_key)

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

    from backend.app.models import Application, PlacementActivity
    app_count = db.query(Application).filter(Application.drive_id == drive_id).count()
    activity_count = db.query(PlacementActivity).filter(PlacementActivity.placement_drive_id == drive_id).count()

    # Prevent accidental hard-deletion if applications or activities exist: archive instead
    if app_count > 0 or activity_count > 0:
        drive.status = "ARCHIVED"
        log = SystemLog(
            user_email=current_user.email,
            action="ARCHIVE_PLACEMENT_DRIVE",
            details=f"Placement drive ID {drive.id} ({drive.role}) has {app_count} application(s) and {activity_count} placement activity record(s). Safely ARCHIVED to preserve historical records."
        )
        db.add(log)
        db.commit()
        return {
            "message": f"Placement drive has {app_count} existing application(s) and {activity_count} activity record(s). It has been safely ARCHIVED instead of deleted to protect historical records.",
            "status": "ARCHIVED",
            "applications_preserved": app_count,
            "activities_preserved": activity_count,
            "archived": True
        }

    log = SystemLog(
        user_email=current_user.email,
        action="DELETE_PLACEMENT_DRIVE",
        details=f"Deleted placement drive ID {drive.id} ({drive.role}) with 0 applications and 0 activities."
    )
    db.add(log)
    db.delete(drive)
    db.commit()
    return {"message": "Placement drive deleted successfully", "archived": False}


@router.put("/api/drives/{drive_id}/archive")
def archive_drive(
    drive_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_permission(current_user, "Placement Drives", "EDIT", db)
    drive = db.query(PlacementDrive).filter(PlacementDrive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Placement drive not found")
    
    from backend.app.models import Application
    app_count = db.query(Application).filter(Application.drive_id == drive_id).count()
    drive.status = "ARCHIVED"
    log = SystemLog(
        user_email=current_user.email,
        action="ARCHIVE_PLACEMENT_DRIVE",
        details=f"Archived placement drive ID {drive.id} ({drive.role}) with {app_count} application(s)."
    )
    db.add(log)
    db.commit()
    return {
        "message": f"Placement drive archived successfully. New applications are disabled, and all {app_count} historical records remain preserved.",
        "id": drive.id,
        "status": "ARCHIVED",
        "applications_count": app_count
    }


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

    from backend.app.models import Application, PlacementDrive
    # Verify no active or archived drives for this company have dependent applications
    drives = db.query(PlacementDrive).filter(PlacementDrive.company_id == company_id).all()
    drive_ids = [d.id for d in drives]
    total_apps = db.query(Application).filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0
    if total_apps > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete company '{company.name}': {total_apps} application(s) exist across its placement drives. Please archive the placement drives instead."
        )
        
    db.delete(company)
    db.commit()
    return {"message": "Company and associated placement drives deleted successfully"}
