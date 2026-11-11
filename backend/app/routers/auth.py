import threading
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, Student, Faculty, Department, Permission, SystemLog
from backend.app.schemas import (
    UserCreate, UserLogin, Token, UserResponse, StudentResponse, FacultyResponse,
    FacultyCreateRequest, FacultyUpdateRequest
)
from backend.app.auth import verify_password, get_password_hash, create_access_token, get_current_user
from backend.app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRateLimiter:
    """
    Sliding-window rate limiter tracking failed authentication attempts per email and client IP.
    Protects against credential stuffing and brute-force attacks.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._attempts: dict[str, dict] = {}

    def _get_key(self, email: str, ip: str) -> str:
        return f"{email.strip().lower()}:{ip.strip()}"

    def check_rate_limit(self, email: str, ip: str):
        key = self._get_key(email, ip)
        now = datetime.utcnow()
        with self._lock:
            record = self._attempts.get(key)
            if not record:
                return

            locked_until = record.get("locked_until")
            if locked_until and now < locked_until:
                remaining_sec = int((locked_until - now).total_seconds())
                minutes = max(1, remaining_sec // 60)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed login attempts. Account temporarily locked. Please try again in {minutes} minute(s).",
                    headers={"Retry-After": str(remaining_sec)}
                )

            window_start = record.get("window_start", now)
            if (now - window_start).total_seconds() > settings.LOGIN_RATE_LIMIT_WINDOW_MINUTES * 60:
                self._attempts.pop(key, None)

    def record_failure(self, email: str, ip: str) -> int:
        key = self._get_key(email, ip)
        now = datetime.utcnow()
        with self._lock:
            record = self._attempts.get(key)
            if not record:
                record = {
                    "failed_attempts": 1,
                    "window_start": now,
                    "locked_until": None
                }
                self._attempts[key] = record
            else:
                record["failed_attempts"] += 1

            failed = record["failed_attempts"]
            if failed >= settings.LOGIN_MAX_FAILED_ATTEMPTS:
                lockout_time = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
                record["locked_until"] = lockout_time
                remaining_sec = int(settings.LOGIN_LOCKOUT_MINUTES * 60)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed login attempts ({failed}/{settings.LOGIN_MAX_FAILED_ATTEMPTS}). Account locked for {settings.LOGIN_LOCKOUT_MINUTES} minutes.",
                    headers={"Retry-After": str(remaining_sec)}
                )
            return settings.LOGIN_MAX_FAILED_ATTEMPTS - failed

    def record_success(self, email: str, ip: str):
        key = self._get_key(email, ip)
        with self._lock:
            self._attempts.pop(key, None)

login_rate_limiter = LoginRateLimiter()

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

@router.post("/login", response_model=Token)
@router.post("/token", response_model=Token)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)
    
    # 1. Check rate limiting before attempting authentication
    login_rate_limiter.check_rate_limit(login_data.email, client_ip)

    # 2. Look up user account
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        remaining = login_rate_limiter.record_failure(login_data.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect email or password. {remaining} attempt(s) remaining before temporary lockout.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Successful authentication: reset rate limiter
    login_rate_limiter.record_success(login_data.email, client_ip)

    # 4. Create and return JWT access token
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "name": user.name,
        "email": user.email
    }

@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Return profile info depending on the role
    response = {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at
    }

    if current_user.role == "student" and current_user.student_profile:
        # Load student profile
        s = current_user.student_profile
        response["student_profile"] = {
            "dept_id": s.dept_id,
            "dept_name": s.department.name,
            "dept_code": s.department.code,
            "gender": s.gender,
            "batch": s.batch,
            "phone": s.phone,
            "cgpa": s.cgpa,
            "attendance": s.attendance,
            "backlogs": s.backlogs,
            "sgpa_sem1": s.sgpa_sem1,
            "sgpa_sem2": s.sgpa_sem2,
            "sgpa_sem3": s.sgpa_sem3,
            "sgpa_sem4": s.sgpa_sem4,
            "sgpa_sem5": s.sgpa_sem5,
            "sgpa_sem6": s.sgpa_sem6,
            "sgpa_sem7": s.sgpa_sem7,
            "sgpa_sem8": s.sgpa_sem8,
            "skills": s.skills,
            "projects": s.projects,
            "internships": s.internships,
            "certifications": s.certifications,
            "github_url": s.github_url,
            "linkedin_url": s.linkedin_url,
            "leetcode_score": s.leetcode_score,
            "codechef_score": s.codechef_score,
            "hackerrank_score": s.hackerrank_score,
            "readiness_score": s.readiness_score,
            "placement_probability": s.placement_probability,
            "ai_recommendations": s.ai_recommendations,
            "status": s.status,
            "profile_completed": s.profile_completed,
            "verification_status": s.verification_status
        }
    elif current_user.role == "faculty" and current_user.faculty_profile:
        f = current_user.faculty_profile
        response["faculty_profile"] = {
            "dept_id": f.dept_id,
            "dept_name": f.department.name,
            "dept_code": f.department.code,
            "designation": f.designation
        }

    return response


@router.get("/faculty")
def get_faculty_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    faculties = db.query(Faculty).all()
    results = []
    for f in faculties:
        results.append({
            "id": f.id,
            "name": f.user.name,
            "email": f.user.email,
            "dept_id": f.dept_id,
            "dept_code": f.department.code,
            "dept_name": f.department.name,
            "designation": f.designation
        })
    return results

@router.post("/faculty")
def create_faculty_account(payload: FacultyCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    pwd_hash = get_password_hash(payload.password)
    user_rec = User(
        email=payload.email,
        password_hash=pwd_hash,
        name=payload.name,
        role="faculty"
    )
    db.add(user_rec)
    db.commit()
    
    faculty_rec = Faculty(
        id=user_rec.id,
        dept_id=payload.dept_id,
        designation=payload.designation
    )
    db.add(faculty_rec)
    db.commit()
    
    return {"message": "Faculty account successfully registered!", "faculty_id": user_rec.id}

@router.put("/faculty/{faculty_id}")
def update_faculty_account(
    faculty_id: int,
    payload: FacultyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied: Admin role required")

    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")

    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Faculty name cannot be empty")

    clean_designation = payload.designation.strip()
    if not clean_designation:
        raise HTTPException(status_code=400, detail="Faculty designation cannot be empty")

    # 1. Validate destination department
    target_dept = db.query(Department).filter(Department.id == payload.dept_id).first()
    if not target_dept:
        raise HTTPException(status_code=400, detail=f"Invalid department ID: {payload.dept_id} does not exist")

    # 2. Update faculty record and synchronize active department-scoped permissions in a single transaction
    try:
        faculty.user.name = clean_name
        faculty.dept_id = target_dept.id
        faculty.designation = clean_designation

        # Synchronize ONLY active department-scoped permissions for this faculty user
        # Uses the actual destination Department.code for permission scope values
        # Preserves inactive, expired, and non-department-scoped permissions (e.g. ALL, SECTION)
        dept_permissions = db.query(Permission).filter(
            Permission.user_id == faculty.user.id,
            Permission.scope == "DEPARTMENT",
            Permission.status == "Active"
        ).all()

        for perm in dept_permissions:
            perm.scope_value = target_dept.code

        # Log administrative action
        log = SystemLog(
            user_email=current_user.email,
            action="UPDATE_FACULTY_COORDINATOR",
            details=f"Faculty ID {faculty.id} updated: Name='{clean_name}', Department={target_dept.code} ({target_dept.id}), Designation='{clean_designation}'. Synchronized {len(dept_permissions)} department permission(s)."
        )
        db.add(log)

        # Single atomic commit
        db.commit()
        db.refresh(faculty)

        return {
            "message": "Faculty details and department permissions synchronized successfully!",
            "faculty_id": faculty.id,
            "dept_id": faculty.dept_id,
            "dept_code": target_dept.code,
            "permissions_updated": len(dept_permissions)
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update faculty account: {str(e)}")

@router.delete("/faculty/{faculty_id}")
def delete_faculty_account(faculty_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
        
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
        
    user_rec = db.query(User).filter(User.id == faculty_id).first()
    
    db.delete(faculty)
    if user_rec:
        db.delete(user_rec)
    db.commit()
    
    return {"message": "Faculty coordinator account deleted successfully"}
