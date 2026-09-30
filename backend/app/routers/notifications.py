from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, Notification
from backend.app.schemas import NotificationResponse
from backend.app.auth import get_current_user
from typing import List, Optional

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_my_notifications(
    page: int = 1,
    limit: int = 20,
    offset: Optional[int] = None,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated notifications for the authenticated user sorted by created_at desc.
    Protects memory against large notification tables (e.g. 33k rows).
    """
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )
    if unread_only:
        query = query.filter(Notification.is_read == False)

    # Cap limit to prevent server-side memory exhaustion (max 100 per page)
    safe_limit = min(max(limit, 1), 100)
    actual_offset = offset if (offset is not None and offset >= 0) else (max(page, 1) - 1) * safe_limit

    return query.order_by(Notification.created_at.desc()).offset(actual_offset).limit(safe_limit).all()

@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notif.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}
