import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import User, Student, Faculty, Parent

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split("$")
        if len(parts) != 2:
            return False
        salt_hex, key_hex = parts
        key = hashlib.pbkdf2_hmac(
            'sha256', 
            plain_password.encode('utf-8'), 
            salt_hex.encode('utf-8'), 
            50000
        )
        return key.hex() == key_hex
    except Exception:
        return False

import secrets

# =============================================================================
# ARCHITECTURAL SECURITY NOTE: localStorage vs. httpOnly Cookies Tradeoff
# =============================================================================
# Currently, AP-CPIP uses Bearer JWT tokens stored in browser localStorage and
# injected via Axios request interceptors (Authorization: Bearer <token>).
#
# TRADEOFF ANALYSIS:
# 1. localStorage (Current Architecture):
#    - Pros: Simpler for decoupled SPAs and cross-origin APIs (CORS). Immune to
#      CSRF (Cross-Site Request Forgery) attacks because browsers do not attach
#      localStorage contents automatically with cross-site requests. Enables
#      stateless multi-client compatibility (web, mobile, CLI, external integrations).
#    - Cons: Vulnerable to XSS (Cross-Site Scripting) if malicious code executes
#      inside the origin and reads window.localStorage.
#
# 2. httpOnly Cookies (Alternative Architecture):
#    - Pros: Cookie cannot be read by JavaScript (mitigates token theft via XSS).
#    - Cons: Vulnerable to CSRF attacks unless strict SameSite flags (Lax/Strict)
#      and anti-CSRF token verification (e.g. Double Submit Cookie pattern) are
#      implemented. Requires tight domain/subdomain alignment and credentials sharing.
#
# RECOMMENDATION / MIGRATION STATUS:
# Switching from localStorage to httpOnly cookies fundamentally changes the
# frontend auth flow (removing localStorage token extraction, adding credentials: true,
# and handling cookie domain scoping). The current implementation mitigates XSS
# through strict React JSX sanitization, parameter validation, and server-side
# token signature/expiration verification. Consult project leads before migration.
# =============================================================================

def get_password_hash(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a secure cryptographically random salt."""
    salt_hex = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt_hex.encode('utf-8'), 
        50000
    )
    return f"{salt_hex}${key.hex()}"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub: str = payload.get("sub")
        role: str = payload.get("role")
        if sub is None or role is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception
        
    if role == "parent":
        # Resolve transient parent user profile
        try:
            student_id = int(sub)
        except ValueError:
            raise credentials_exception
        parent = db.query(Parent).filter(Parent.student_id == student_id).first()
        if not parent:
            raise credentials_exception
        return User(
            id=parent.id,
            email=f"parent_{student_id}@platform.edu",
            name=parent.parent_name,
            role="parent",
            created_at=datetime.utcnow()
        )
        
    user = db.query(User).filter(User.email == sub).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_student(user: User = Depends(get_current_user)) -> Student:
    if user.role != "student" or not user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Student role required"
        )
    return user.student_profile

def get_current_faculty(user: User = Depends(get_current_user)) -> Faculty:
    if user.role not in ["faculty", "admin"] or not user.faculty_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Faculty or Admin role required"
        )
    return user.faculty_profile

def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin role required"
        )
    return user


def verify_permission(user: User, module: str, action: str, db: Session):
    if user.role == "admin":
        return {"scope": "ALL", "scope_value": None}

    if user.role == "tnp":
        if module == "Access Control":
            raise HTTPException(status_code=403, detail="TNP cannot edit system permissions")
        return {"scope": "ALL", "scope_value": None}

    # 1. Check for active elevated grant in the permissions table (e.g. ALL scope, cross-dept, or CREATE/EDIT/DELETE/EXPORT)
    from backend.app.models import Permission
    now = datetime.utcnow()

    module_aliases = {
        "Student Performance": ["Student Performance", "students", "Analytics", "analytics"],
        "students": ["Student Performance", "students", "Analytics", "analytics"],
        "Placement Drives": ["Placement Drives", "drives"],
        "drives": ["Placement Drives", "drives"],
        "Analytics": ["Student Performance", "students", "Analytics", "analytics"],
        "analytics": ["Student Performance", "students", "Analytics", "analytics"]
    }
    modules_to_check = module_aliases.get(module, [module])

    action_aliases = {
        "VIEW": ["VIEW", "READ"],
        "READ": ["VIEW", "READ"],
        "EDIT": ["EDIT", "UPDATE", "WRITE"],
        "UPDATE": ["EDIT", "UPDATE", "WRITE"],
        "CREATE": ["CREATE", "ADD"],
        "DELETE": ["DELETE"]
    }
    actions_to_check = [a.upper() for a in action_aliases.get(action.upper(), [action.upper()])]

    perms = db.query(Permission).filter(
        Permission.user_id == user.id,
        Permission.module.in_(modules_to_check),
        Permission.status == "Active",
        Permission.start_date <= now,
        Permission.expiry_date >= now
    ).all()

    for perm in perms:
        allowed_actions = [act.strip().upper() for act in perm.action.split(",")]
        if any(act in allowed_actions for act in actions_to_check):
            return {"scope": perm.scope, "scope_value": perm.scope_value}

    # 2. Baseline role capability: Faculty and HOD roles have automatic department-scoped VIEW/READ access
    # to Student Performance, Analytics, and Placement Drives data without requiring a manual grant in the permissions table.
    # Elevated actions (EDIT, CREATE, DELETE, EXPORT) or cross-department scopes still strictly require an active grant in permissions.
    if user.role in ["faculty", "hod"] and action.upper() in ["VIEW", "READ"]:
        if module in ["Student Performance", "students", "Analytics", "analytics", "Placement Drives", "drives"]:
            dept_id = user.faculty_profile.dept_id if user.faculty_profile else None
            if dept_id:
                return {"scope": "DEPARTMENT", "scope_value": str(dept_id)}

    if not perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: No active permission for module '{module}'"
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied: Action '{action}' not authorized for module '{module}'"
    )


def enforce_student_scope(user: User, student_id: int, db: Session, action: str = "VIEW") -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    if user.role == "parent":
        # Determine parent's child ID from database
        parent = db.query(Parent).filter(Parent.id == user.id).first()
        if not parent or parent.student_id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Parent can only access their child's data"
            )
    elif user.role == "student":
        if user.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Students can only access their own data"
            )
    elif user.role in ["faculty", "hod"]:
        scope_info = verify_permission(user, "Student Performance", action, db)
        scope = scope_info.get("scope")
        scope_val = scope_info.get("scope_value")
        
        if scope == "DEPARTMENT":
            is_match = False
            if str(scope_val).isdigit():
                is_match = (student.dept_id == int(scope_val))
            else:
                is_match = (student.department.code.upper() == str(scope_val).upper())
            if not is_match:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: outside department scope ({scope_val})"
                )
        elif scope == "SECTION":
            if student.section.upper() != str(scope_val).upper():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: outside section scope ({scope_val})"
                )
        elif scope == "ALL":
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: unauthorized scope value"
            )
    elif user.role == "tnp":
        pass
    elif user.role == "admin":
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: unauthorized role"
        )
    return student


def get_permitted_student_query(user: User, db: Session, action: str = "VIEW"):
    from backend.app.models import Department
    if user.role in ["admin", "tnp"]:
        return db.query(Student)
    elif user.role == "student":
        return db.query(Student).filter(Student.id == user.id)
    elif user.role == "parent":
        parent = db.query(Parent).filter(Parent.id == user.id).first()
        if not parent:
            return db.query(Student).filter(Student.id == -1)
        return db.query(Student).filter(Student.id == parent.student_id)
    elif user.role in ["faculty", "hod"]:
        scope_info = verify_permission(user, "Student Performance", action, db)
        scope = scope_info.get("scope")
        scope_val = scope_info.get("scope_value")
        
        if scope == "DEPARTMENT":
            if str(scope_val).isdigit():
                return db.query(Student).filter(Student.dept_id == int(scope_val))
            else:
                return db.query(Student).join(Department).filter(Department.code == scope_val)
        elif scope == "SECTION":
            return db.query(Student).filter(Student.section == scope_val)
        elif scope == "ALL":
            return db.query(Student)
        else:
            return db.query(Student).filter(Student.id == -1)
    else:
        return db.query(Student).filter(Student.id == -1)
