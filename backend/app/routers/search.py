from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, Student, PlacementDrive, Company, Parent, Application, PlacementActivity
from backend.app.auth import get_current_user, get_permitted_student_query, verify_permission
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/search", tags=["Global Search"])

@router.get("")
def global_search(
    q: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform a unified scoped search across candidates, drives, companies, applications, and activities.
    Enforces server-side permissions and scoping rules.
    """
    if current_user.role not in ["faculty", "admin", "parent", "hod", "tnp"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Global Search is restricted to officers, faculty, and parent coordinators."
        )

    if not q:
        return {"students": [], "drives": [], "companies": [], "applications": [], "activities": []}

    results = {
        "students": [],
        "drives": [],
        "companies": [],
        "applications": [],
        "activities": []
    }

    # 1. Scoped Student Search
    try:
        student_query = get_permitted_student_query(current_user, db, "VIEW")
        
        # Try searching by exact ID (roll number) or name/email substring
        try:
            roll_num = int(q)
            student_query = student_query.filter(Student.id == roll_num)
        except ValueError:
            student_query = student_query.join(User).filter(
                (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
            )
            
        students = student_query.limit(20).all()
        for s in students:
            results["students"].append({
                "id": s.id,
                "name": s.user.name,
                "email": s.user.email,
                "dept_code": s.department.code,
                "cgpa": s.cgpa,
                "status": s.status
            })
    except HTTPException:
        results["students"] = []

    # 2. Scoped Placement Drives Search
    user_dept_code = None
    user_batch = None
    if current_user.role == "parent":
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

    try:
        all_matching_drives = db.query(PlacementDrive).join(Company).filter(
            (PlacementDrive.role.ilike(f"%{q}%")) | (Company.name.ilike(f"%{q}%"))
        ).all()

        visible_drives_count = 0
        for d in all_matching_drives:
            if visible_drives_count >= 20:
                break
                
            is_visible = False
            allowed_depts = [dept.strip().upper() for dept in d.allowed_depts.split(",")]
            
            if current_user.role in ["admin", "tnp"]:
                is_visible = True
            elif current_user.role == "parent":
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
                results["drives"].append({
                    "id": d.id,
                    "company_name": d.company.name,
                    "role": d.role,
                    "package_lpa": d.package_lpa,
                    "status": d.status
                })
                visible_drives_count += 1
    except Exception:
        results["drives"] = []

    # 3. Companies Search
    try:
        companies = db.query(Company).filter(
            Company.name.ilike(f"%{q}%")
        ).limit(20).all()
        
        for c in companies:
            results["companies"].append({
                "id": c.id,
                "name": c.name,
                "industry": c.industry,
                "website": c.website
            })
    except Exception:
        results["companies"] = []

    # 4. Scoped Applications Search
    try:
        app_query = db.query(Application).join(Student).join(User, Student.id == User.id).join(PlacementDrive).join(Company)
        
        # Restrict applications by student query scope
        if current_user.role in ["faculty", "hod"]:
            permitted_student_ids = get_permitted_student_query(current_user, db, "VIEW").with_entities(Student.id)
            app_query = app_query.filter(Application.student_id.in_(permitted_student_ids))
        elif current_user.role == "parent":
            parent = db.query(Parent).filter(Parent.id == current_user.id).first()
            if parent:
                app_query = app_query.filter(Application.student_id == parent.student_id)
            else:
                app_query = app_query.filter(Application.id == -1)
                
        # Apply query filtering
        app_query = app_query.filter(
            (User.name.ilike(f"%{q}%")) | 
            (Company.name.ilike(f"%{q}%")) | 
            (PlacementDrive.role.ilike(f"%{q}%"))
        )
        
        apps = app_query.limit(20).all()
        for ap in apps:
            results["applications"].append({
                "id": ap.id,
                "student_name": ap.student.user.name,
                "company_name": ap.drive.company.name,
                "role": ap.drive.role,
                "status": ap.status,
                "current_round": ap.current_round
            })
    except HTTPException:
        results["applications"] = []

    # 5. Scoped Activities Search
    try:
        activities_query = db.query(PlacementActivity).filter(
            (PlacementActivity.activity_name.ilike(f"%{q}%")) | (PlacementActivity.activity_type.ilike(f"%{q}%"))
        )
        all_matching_activities = activities_query.all()
        
        visible_activities_count = 0
        for act in all_matching_activities:
            if visible_activities_count >= 20:
                break
                
            is_visible = False
            if not act.placement_drive_id:
                # General activities visible
                is_visible = True
            else:
                d = act.drive
                if d:
                    allowed_depts = [dept.strip().upper() for dept in d.allowed_depts.split(",")]
                    if current_user.role in ["admin", "tnp"]:
                        is_visible = True
                    elif current_user.role == "parent":
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
                results["activities"].append({
                    "id": act.id,
                    "name": act.activity_name,
                    "activity_type": act.activity_type,
                    "date": act.date.isoformat() if act.date else None
                })
                visible_activities_count += 1
    except Exception:
        results["activities"] = []

    return results
