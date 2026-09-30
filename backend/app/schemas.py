from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str
    email: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# Department
class DepartmentBase(BaseModel):
    name: str
    code: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# User
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class UserResponse(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Student Project Schema
class ProjectSchema(BaseModel):
    title: str
    description: str
    skills_used: List[str]

# Student Certification Schema
class CertificationSchema(BaseModel):
    name: str
    issuer: str
    date_obtained: str

# Student Internship Schema
class InternshipSchema(BaseModel):
    company: str
    role: str
    duration: str
    description: str

# Student Details
class StudentBase(BaseModel):
    gender: str
    batch: str
    section: Optional[str] = "A"
    phone: Optional[str] = None
    cgpa: float
    attendance: float
    backlogs: int = 0
    sgpa_sem1: Optional[float] = None
    sgpa_sem2: Optional[float] = None
    sgpa_sem3: Optional[float] = None
    sgpa_sem4: Optional[float] = None
    sgpa_sem5: Optional[float] = None
    sgpa_sem6: Optional[float] = None
    sgpa_sem7: Optional[float] = None
    sgpa_sem8: Optional[float] = None
    skills: Optional[str] = None  # JSON string representation
    projects: Optional[str] = None  # JSON string representation
    internships: Optional[str] = None  # JSON string representation
    certifications: Optional[str] = None  # JSON string representation
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    leetcode_score: Optional[int] = 0
    codechef_score: Optional[int] = 0
    hackerrank_score: Optional[int] = 0

class StudentCreate(StudentBase):
    dept_id: int

class StudentUpdate(BaseModel):
    phone: Optional[str] = None
    cgpa: Optional[float] = None
    attendance: Optional[float] = None
    backlogs: Optional[int] = None
    sgpa_sem1: Optional[float] = None
    sgpa_sem2: Optional[float] = None
    sgpa_sem3: Optional[float] = None
    sgpa_sem4: Optional[float] = None
    sgpa_sem5: Optional[float] = None
    sgpa_sem6: Optional[float] = None
    sgpa_sem7: Optional[float] = None
    sgpa_sem8: Optional[float] = None
    skills: Optional[str] = None
    projects: Optional[str] = None
    internships: Optional[str] = None
    certifications: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    leetcode_score: Optional[int] = None
    codechef_score: Optional[int] = None
    hackerrank_score: Optional[int] = None
    resume_path: Optional[str] = None
    resume_text: Optional[str] = None
    resume_ats_score: Optional[int] = None
    resume_analysis_json: Optional[str] = None

class StudentResponse(StudentBase):
    id: int
    dept_id: int
    user: UserResponse
    department: DepartmentResponse
    readiness_score: float
    placement_probability: float
    ai_recommendations: Optional[str] = None
    status: str
    profile_completed: bool
    verification_status: str
    resume_text: Optional[str] = None
    resume_ats_score: Optional[int] = 0
    resume_analysis_json: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Faculty Details
class FacultyBase(BaseModel):
    designation: str

class FacultyCreate(FacultyBase):
    dept_id: int

class FacultyResponse(FacultyBase):
    id: int
    dept_id: int
    user: UserResponse
    department: DepartmentResponse
    model_config = ConfigDict(from_attributes=True)

# Company
class CompanyBase(BaseModel):
    name: str
    industry: str
    website: Optional[str] = None
    description: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Placement Drive
class PlacementDriveBase(BaseModel):
    role: str
    package_lpa: float
    location: str
    cgpa_cutoff: float
    allowed_depts: str  # e.g., "CSE,ECE"
    allowed_backlogs: int = 0
    bond_details: Optional[str] = None
    selection_process: Optional[str] = None
    interview_date: date
    deadline: date
    status: str = "DRAFT"
    min_attendance: Optional[float] = 75.0
    batch: Optional[str] = "2026"
    
    # JD additions
    job_id: Optional[str] = None
    responsibilities: Optional[str] = None
    required_skills: Optional[str] = None
    preferred_skills: Optional[str] = None
    job_type: Optional[str] = "Full-Time"
    work_mode: Optional[str] = "Onsite"
    openings_count: Optional[int] = 5
    hiring_process: Optional[str] = None
    jd_pdf_path: Optional[str] = None
    company_logo: Optional[str] = None

class PlacementDriveCreate(PlacementDriveBase):
    company_id: Optional[int] = None
    company_name: Optional[str] = None

class PlacementDriveResponse(PlacementDriveBase):
    id: int
    company_id: int
    company: CompanyResponse
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PlacementDriveUpdateResponse(PlacementDriveBase):
    id: int
    company_id: int
    company_name: Optional[str] = ""
    lifecycle_status: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# Applications
class ApplicationBase(BaseModel):
    status: str = "Applied"
    current_round: str = "Applied"
    joining_status: str = "Pending"
    remarks: Optional[str] = None

class ApplicationCreate(BaseModel):
    drive_id: int

class ApplicationStatusUpdate(BaseModel):
    status: str
    current_round: str
    joining_status: Optional[str] = "Pending"
    remarks: Optional[str] = None

class ApplicationResponse(ApplicationBase):
    id: int
    student_id: int
    drive_id: int
    applied_date: datetime
    drive: PlacementDriveResponse
    model_config = ConfigDict(from_attributes=True)

class ApplicationWithStudentResponse(ApplicationResponse):
    student: StudentResponse
    model_config = ConfigDict(from_attributes=True)

# Interviews
class InterviewBase(BaseModel):
    round_name: str
    status: str = "Scheduled"
    interview_date: datetime
    remarks: Optional[str] = None

class InterviewCreate(InterviewBase):
    application_id: int

class InterviewResponse(InterviewBase):
    id: int
    application_id: int
    student_id: int
    model_config = ConfigDict(from_attributes=True)

# Feedbacks
class FeedbackBase(BaseModel):
    experience_text: str
    questions_asked: Optional[str] = None
    difficulty_rating: int = 3
    preparation_time: Optional[str] = None
    suggestions: Optional[str] = None

class FeedbackCreate(FeedbackBase):
    interview_id: Optional[int] = None

class FeedbackResponse(FeedbackBase):
    id: int
    interview_id: int
    sentiment_score: float
    extracted_keywords: Optional[str] = None
    topic_analysis: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Notifications
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Logs
class SystemLogResponse(BaseModel):
    id: int
    user_email: str
    action: str
    details: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# AI Analytics Output Schema
class AIReadinessReport(BaseModel):
    readiness_score: float
    placement_probability: float
    skills_gap: List[str]
    recommended_skills: List[str]
    recommended_projects: List[str]
    recommended_certifications: List[str]
    matching_companies: List[Dict[str, Any]]
    explanation: str
    at_risk: bool
    risk_reason: Optional[str] = None
    improvement_tips: List[str]

# Parent Portals
class ParentOTPRequest(BaseModel):
    roll_number: int
    mobile_number: str

class ParentOTPVerify(BaseModel):
    roll_number: int
    mobile_number: str
    otp: str

# Correction requests
class CorrectionRequestCreate(BaseModel):
    field: str
    current_value: str
    requested_value: str
    reason: str

class CorrectionRequestAction(BaseModel):
    status: str # "Approved" or "Rejected"

class CorrectionRequestResponse(BaseModel):
    id: int
    student_id: int
    field: str
    current_value: str
    requested_value: str
    reason: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Access Permissions
class PermissionCreate(BaseModel):
    user_id: int
    module: str
    scope: str
    scope_value: Optional[str] = None
    action: str
    duration_days: int

class PermissionResponse(BaseModel):
    id: int
    user_id: int
    module: str
    scope: str
    scope_value: Optional[str] = None
    action: str
    start_date: datetime
    expiry_date: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)

class AccessRequestCreate(BaseModel):
    module: str
    scope: str
    scope_value: Optional[str] = None
    action: str
    duration_days: int
    reason: str

class AccessRequestAction(BaseModel):
    status: str # "Approved" or "Rejected"

class AccessRequestResponse(BaseModel):
    id: int
    user_id: int
    module: str
    scope: str
    scope_value: Optional[str] = None
    action: str
    duration_days: int
    reason: str
    status: str
    model_config = ConfigDict(from_attributes=True)

# Placement Activities
class PlacementActivityCreate(BaseModel):
    placement_drive_id: Optional[int] = None
    company_id: Optional[int] = None
    activity_name: str
    activity_type: str
    date: date
    start_time: str
    end_time: str
    location: str
    description: Optional[str] = None
    mandatory: Optional[bool] = True

class PlacementActivityResponse(BaseModel):
    id: int
    placement_drive_id: Optional[int] = None
    company_id: Optional[int] = None
    activity_name: str
    activity_type: str
    date: date
    start_time: str
    end_time: str
    location: str
    description: Optional[str] = None
    mandatory: bool
    model_config = ConfigDict(from_attributes=True)

class ActivityAttendanceMark(BaseModel):
    student_id: int
    status: str # "PRESENT" or "ABSENT"
    remarks: Optional[str] = None

class ActivityAttendanceResponse(BaseModel):
    id: int
    activity_id: int
    student_id: int
    status: str
    remarks: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Grievance
class GrievanceCreate(BaseModel):
    category: str
    title: str
    description: str

class GrievanceResponse(BaseModel):
    id: int
    student_id: int
    category: str
    title: str
    description: str
    status: str
    created_at: datetime
    resolution_remarks: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
