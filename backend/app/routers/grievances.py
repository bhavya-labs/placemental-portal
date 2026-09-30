from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, Student, Grievance
from backend.app.schemas import GrievanceCreate, GrievanceResponse
from backend.app.auth import get_current_user, verify_permission
from typing import List, Optional

router = APIRouter(prefix="/api/grievances", tags=["Grievances & Issue Management"])

@router.post("", response_model=GrievanceResponse)
def submit_grievance(
    payload: GrievanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can report grievances")
        
    grievance = Grievance(
        student_id=current_user.id,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        status="OPEN"
    )
    db.add(grievance)
    db.commit()
    db.refresh(grievance)
    return grievance

@router.get("", response_model=List[GrievanceResponse])
def list_grievances(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "student":
        return db.query(Grievance).filter(Grievance.student_id == current_user.id).order_by(Grievance.created_at.desc()).all()
        
    if current_user.role in ["admin", "tnp"]:
        return db.query(Grievance).order_by(Grievance.created_at.desc()).all()
        
    if current_user.role in ["faculty", "hod"]:
        try:
            scope_info = verify_permission(current_user, "Student Performance", "VIEW", db)
        except HTTPException:
            return []
            
        query = db.query(Grievance).join(Student)
        if scope_info["scope"] == "DEPARTMENT":
            from backend.app.models import Department
            if str(scope_info["scope_value"]).isdigit():
                query = query.filter(Student.dept_id == int(scope_info["scope_value"]))
            else:
                query = query.join(Department, Student.dept_id == Department.id).filter(Department.code == scope_info["scope_value"])
        elif scope_info["scope"] == "SECTION":
            query = query.filter(Student.section == scope_info["scope_value"])
        return query.order_by(Grievance.created_at.desc()).all()
        
    return []

@router.put("/{grievance_id}/status")
def resolve_grievance(
    grievance_id: int,
    status: str,
    remarks: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only Admin, TNP, and HODs/Faculty can resolve grievances
    if current_user.role not in ["admin", "tnp", "faculty", "hod"]:
        raise HTTPException(status_code=403, detail="Access denied")
        
    grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")
        
    # Check permissions
    if current_user.role in ["faculty", "hod"]:
        verify_permission(current_user, "Student Performance", "EDIT", db)
        
    if status.upper() not in ["OPEN", "UNDER_REVIEW", "RESOLVED"]:
        raise HTTPException(status_code=400, detail="Invalid status transition")
        
    grievance.status = status.upper()
    if remarks:
        grievance.resolution_remarks = remarks
        
    # Trigger student notification (Req 12)
    from backend.app.models import Notification
    db.add(Notification(
        user_id=grievance.student_id,
        title="Grievance Status Updated",
        message=f"Your grievance titled '{grievance.title}' has been updated to '{status.upper()}'."
    ))
        
    db.commit()
    return {"message": f"Grievance status updated to {status.upper()}"}
