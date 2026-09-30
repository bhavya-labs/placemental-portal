import threading
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, Student, Faculty, Department
from backend.app.schemas import UserCreate, UserLogin, Token, UserResponse, StudentResponse, FacultyResponse
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

from pydantic import BaseModel

class FacultyCreateRequest(BaseModel):
    name: str
    email: str
    password: str = "password123"
    dept_id: int
    designation: str

class FacultyUpdateRequest(BaseModel):
    name: str
    dept_id: int
    designation: str

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
def update_faculty_account(faculty_id: int, payload: FacultyUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
        
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
        
    faculty.user.name = payload.name
    faculty.dept_id = payload.dept_id
    faculty.designation = payload.designation
    db.commit()
    
    return {"message": "Faculty details modified successfully!"}

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
