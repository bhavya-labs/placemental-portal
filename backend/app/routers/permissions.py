from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from backend.app.database import get_db
from backend.app.models import User, Permission, AccessRequest, SystemLog
from backend.app.schemas import PermissionCreate, PermissionResponse, AccessRequestCreate, AccessRequestResponse, AccessRequestAction
from backend.app.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/api/permissions", tags=["Access Management"])

@router.get("", response_model=List[PermissionResponse])
def list_permissions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required")
    # Clean expired permissions on the fly
    now = datetime.utcnow()
    db.query(Permission).filter(Permission.expiry_date < now, Permission.status == "Active").update({"status": "Expired"})
    db.commit()
    return db.query(Permission).all()

@router.post("/grant", response_model=PermissionResponse)
def grant_permission(req: PermissionCreate, current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    target_user = db.query(User).filter(User.id == req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user account not found")

    now = datetime.utcnow()
    expiry = now + timedelta(days=req.duration_days)
    
    perm = Permission(
        user_id=req.user_id,
        module=req.module,
        scope=req.scope,
        scope_value=req.scope_value,
        action=req.action,
        start_date=now,
        expiry_date=expiry,
        status="Active"
    )
    db.add(perm)
    
    # Audit log
    audit = SystemLog(
        user_email=current_user.email,
        action="GRANT_PERMISSION",
        details=f"Granted {req.action} on module {req.module} to {target_user.email} (Scope: {req.scope}:{req.scope_value}, Duration: {req.duration_days} days)"
    )
    db.add(audit)
    db.commit()
    db.refresh(perm)
    return perm

@router.post("/revoke/{permission_id}")
def revoke_permission(permission_id: int, current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    perm = db.query(Permission).filter(Permission.id == permission_id).first()
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
        
    perm.status = "Revoked"
    perm.expiry_date = datetime.utcnow()
    
    # Audit log
    audit = SystemLog(
        user_email=current_user.email,
        action="REVOKE_PERMISSION",
        details=f"Revoked permission ID {permission_id} for user ID {perm.user_id}"
    )
    db.add(audit)
    db.commit()
    return {"message": "Permission successfully revoked"}

@router.post("/requests", response_model=AccessRequestResponse)
def create_access_request(req: AccessRequestCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["faculty", "hod", "tnp"]:
        raise HTTPException(status_code=403, detail="Only coordinators can request additional permission scopes")
        
    request = AccessRequest(
        user_id=current_user.id,
        module=req.module,
        scope=req.scope,
        scope_value=req.scope_value,
        action=req.action,
        duration_days=req.duration_days,
        reason=req.reason,
        status="Pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

@router.get("/requests", response_model=List[AccessRequestResponse])
def list_access_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "admin":
        return db.query(AccessRequest).all()
    # Faculty/HODs only view their own requests
    return db.query(AccessRequest).filter(AccessRequest.user_id == current_user.id).all()

@router.put("/requests/{request_id}/action")
def action_access_request(request_id: int, action_data: AccessRequestAction, current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    req = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Access request not found")

    if req.status != "Pending":
        raise HTTPException(status_code=400, detail="Request has already been processed")

    req.status = action_data.status
    
    if action_data.status == "Approved":
        # Create Permission row
        now = datetime.utcnow()
        expiry = now + timedelta(days=req.duration_days)
        perm = Permission(
            user_id=req.user_id,
            module=req.module,
            scope=req.scope,
            scope_value=req.scope_value,
            action=req.action,
            start_date=now,
            expiry_date=expiry,
            status="Active"
        )
        db.add(perm)
        
    # Audit log
    audit = SystemLog(
        user_email=current_user.email,
        action=f"ACCESS_REQUEST_{action_data.status.upper()}",
        details=f"Processed request ID {request_id} for user ID {req.user_id} - Result: {action_data.status}"
    )
    db.add(audit)
    db.commit()
    return {"message": f"Request status updated to {action_data.status}"}
