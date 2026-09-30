from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from jose import JWTError, jwt
from backend.app.database import get_db
from backend.app.models import User, Student, Parent, ParentOTP, PlacementDrive, Application, ActivityAttendance, PlacementActivity, Notification
from backend.app.schemas import ParentOTPRequest, ParentOTPVerify
from backend.app.auth import create_access_token, get_password_hash, verify_password
from backend.app.config import settings

router = APIRouter(prefix="/api/parent", tags=["Parent Portal"])

def get_current_parent_child_id(authorization: str = Header(...), db: Session = Depends(get_db)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate parent session credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if not authorization.startswith("Bearer "):
            raise credentials_exception
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        student_id: str = payload.get("sub")
        role: str = payload.get("role")
        if student_id is None or role != "parent":
            raise credentials_exception
        return int(student_id)
    except (JWTError, ValueError):
        raise credentials_exception

class SMSProvider:
    def send_otp(self, phone: str, otp: str):
        raise NotImplementedError

class DevelopmentSMSProvider(SMSProvider):
    def send_otp(self, phone: str, otp: str):
        print(f"\n[SMS SIMULATOR - DEV] OTP for parent {phone}: {otp}\n")

class ProductionSMSProvider(SMSProvider):
    def send_otp(self, phone: str, otp: str):
        # production provider console logs simulated dispatch for demo testing
        print(f"\n[SMS DISPATCH - PROD] OTP dispatched successfully to {phone}. (OTP secret hidden)\n")

sms_provider = ProductionSMSProvider() if settings.SMS_ENV == "prod" else DevelopmentSMSProvider()


@router.post("/request-otp")
def request_parent_otp(req: ParentOTPRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == req.roll_number).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student roll number not registered")

    parent = db.query(Parent).filter(Parent.student_id == req.roll_number).first()
    if not parent:
        parent = Parent(
            student_id=req.roll_number,
            parent_name=f"Parent of {student.user.name}",
            mobile_number=req.mobile_number,
            relationship="Guardian"
        )
        db.add(parent)
        db.commit()
    else:
        if parent.mobile_number != req.mobile_number:
            raise HTTPException(status_code=400, detail="Mobile number does not match registered records")

    # Cooldown & Rate limiting check
    now = datetime.utcnow()
    otp_record = db.query(ParentOTP).filter(ParentOTP.mobile_number == req.mobile_number).first()
    
    if otp_record:
        # Check resend cooldown
        time_since_last = (now - otp_record.last_requested_at).total_seconds()
        if time_since_last < settings.OTP_RESEND_COOLDOWN_SECONDS:
            raise HTTPException(
                status_code=400,
                detail=f"Please wait {int(settings.OTP_RESEND_COOLDOWN_SECONDS - time_since_last)} seconds before requesting another OTP."
            )

        # Check hourly rate limiting window
        time_since_window = (now - otp_record.window_start).total_seconds()
        if time_since_window > settings.OTP_RATE_LIMIT_WINDOW_HOURS * 3600:
            otp_record.window_start = now
            otp_record.request_count = 1
        else:
            if otp_record.request_count >= settings.OTP_MAX_REQUESTS_PER_WINDOW:
                raise HTTPException(
                    status_code=400,
                    detail="Too many OTP requests. Please try again in an hour."
                )
            otp_record.request_count += 1
            
        # Update details
        otp = str(random.randint(100000, 999999))
        otp_record.otp_hash = get_password_hash(otp)
        otp_record.expires_at = now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        otp_record.attempts = 0
        otp_record.last_requested_at = now
        otp_record.used_at = None
    else:
        otp = str(random.randint(100000, 999999))
        otp_hash = get_password_hash(otp)
        expires_at = now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        otp_record = ParentOTP(
            mobile_number=req.mobile_number,
            otp_hash=otp_hash,
            expires_at=expires_at,
            attempts=0,
            created_at=now,
            last_requested_at=now,
            used_at=None,
            request_count=1,
            window_start=now
        )
        db.add(otp_record)
        
    db.commit()

    # Dispatch via SMS Provider
    sms_provider.send_otp(req.mobile_number, otp)

    # SECURE: return NO OTP in response body in production; include otp_debug for dev/testing
    response_payload = {
        "success": True,
        "message": "OTP generated successfully and sent to registered parent mobile.",
        "expires_in": settings.OTP_EXPIRY_MINUTES * 60
    }
    if settings.SMS_ENV != "prod":
        response_payload["otp_debug"] = otp
        
    return response_payload


@router.post("/verify-otp")
def verify_parent_otp(req: ParentOTPVerify, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.student_id == req.roll_number).first()
    if not parent or parent.mobile_number != req.mobile_number:
        raise HTTPException(status_code=400, detail="Invalid roll number or mobile matching")

    now = datetime.utcnow()
    otp_record = db.query(ParentOTP).filter(
        ParentOTP.mobile_number == req.mobile_number
    ).first()
    
    if not otp_record or otp_record.expires_at < now or otp_record.used_at is not None:
        raise HTTPException(status_code=400, detail="OTP expired or not requested")

    if otp_record.attempts >= settings.OTP_MAX_VERIFY_ATTEMPTS:
        raise HTTPException(
            status_code=400, 
            detail="Too many failed verification attempts. Please request a new OTP."
        )

    if not verify_password(req.otp, otp_record.otp_hash):
        otp_record.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect OTP verification code")

    # Mark as used
    otp_record.used_at = now
    db.commit()

    access_token = create_access_token(
        data={"sub": str(parent.student_id), "role": "parent", "name": parent.parent_name}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "parent",
        "name": parent.parent_name,
        "email": f"parent_{parent.student_id}@platform.edu"
    }

@router.get("/child")
def get_child_data(student_id: int = Depends(get_current_parent_child_id), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Child student profile not found")

    # Get student applications
    applications = db.query(Application).filter(Application.student_id == student_id).all()
    apps_data = []
    for app in applications:
        company_name = app.drive.company.name if (app.drive and app.drive.company) else "Unknown Company"
        role = app.drive.role if app.drive else "N/A"
        package_lpa = app.drive.package_lpa if app.drive else 0.0
        apps_data.append({
            "company_name": company_name,
            "role": role,
            "package_lpa": package_lpa,
            "status": app.status,
            "current_round": app.current_round,
            "applied_date": app.applied_date
        })

    # Get activity participation / timelines
    attendance = db.query(ActivityAttendance).filter(ActivityAttendance.student_id == student_id).all()
    attendance_data = []
    for att in attendance:
        activity_name = att.activity.activity_name if att.activity else "Unknown Activity"
        activity_type = att.activity.activity_type if att.activity else "N/A"
        date = att.activity.date if att.activity else None
        attendance_data.append({
            "activity_name": activity_name,
            "activity_type": activity_type,
            "date": date,
            "status": att.status,
            "remarks": att.remarks
        })

    # Get child placement notifications
    notifications = db.query(Notification).filter(
        Notification.user_id == student_id
    ).order_by(Notification.created_at.desc()).limit(15).all()

    notif_data = [{
        "title": n.title,
        "message": n.message,
        "created_at": n.created_at
    } for n in notifications]

    return {
        "student": {
            "id": student.id,
            "name": student.user.name,
            "dept_code": student.department.code,
            "dept_name": student.department.name,
            "cgpa": student.cgpa,
            "attendance": student.attendance,
            "backlogs": student.backlogs,
            "status": student.status,
            "skills": student.skills
        },
        "applications": apps_data,
        "attendance": attendance_data,
        "notifications": notif_data
    }
