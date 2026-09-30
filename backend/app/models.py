from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Date, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False)

    students = relationship("Student", back_populates="department")
    faculty = relationship("Faculty", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, index=True)  # student, faculty, admin, tnp, hod, parent
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student_profile = relationship("Student", uselist=False, back_populates="user", cascade="all, delete-orphan")
    faculty_profile = relationship("Faculty", uselist=False, back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    gender = Column(String, nullable=False)
    batch = Column(String, nullable=False, index=True)  # e.g., 2026
    phone = Column(String, nullable=True)

    # Academics
    cgpa = Column(Float, nullable=False, default=0.0, index=True)
    attendance = Column(Float, nullable=False, default=0.0)
    backlogs = Column(Integer, nullable=False, default=0)
    sgpa_sem1 = Column(Float, nullable=True)
    sgpa_sem2 = Column(Float, nullable=True)
    sgpa_sem3 = Column(Float, nullable=True)
    sgpa_sem4 = Column(Float, nullable=True)
    sgpa_sem5 = Column(Float, nullable=True)
    sgpa_sem6 = Column(Float, nullable=True)
    sgpa_sem7 = Column(Float, nullable=True)
    sgpa_sem8 = Column(Float, nullable=True)

    # Technical Profiles & Data
    skills = Column(Text, nullable=True)  # JSON string of skills
    projects = Column(Text, nullable=True)  # JSON string of projects
    internships = Column(Text, nullable=True)  # JSON string of internships
    certifications = Column(Text, nullable=True)  # JSON string of certifications
    resume_path = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    
    # Coding scores
    leetcode_score = Column(Integer, default=0)
    codechef_score = Column(Integer, default=0)
    hackerrank_score = Column(Integer, default=0)

    # AI Predictions & Metrics
    readiness_score = Column(Float, default=0.0)
    placement_probability = Column(Float, default=0.0)
    ai_recommendations = Column(Text, nullable=True)  # JSON recommendations
    status = Column(String, default="Unplaced", index=True)  # Placed, Unplaced, At Risk
    profile_completed = Column(Boolean, default=False)
    verification_status = Column(String, default="UNVERIFIED", index=True)
    section = Column(String, default="A")
    portfolio_url = Column(String, nullable=True)
    career_preferences = Column(String, nullable=True)
    
    # Resume scanning parameters
    resume_text = Column(Text, nullable=True)
    resume_ats_score = Column(Integer, default=0)
    resume_analysis_json = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    department = relationship("Department", back_populates="students")
    applications = relationship("Application", back_populates="student", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="student", cascade="all, delete-orphan")


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    designation = Column(String, nullable=False)

    # Relationships
    user = relationship("User", back_populates="faculty_profile")
    department = relationship("Department", back_populates="faculty")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    industry = Column(String, nullable=False)
    website = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    drives = relationship("PlacementDrive", back_populates="company", cascade="all, delete-orphan")


class PlacementDrive(Base):
    __tablename__ = "placement_drives"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False)
    package_lpa = Column(Float, nullable=False)  # in Lakhs Per Annum
    location = Column(String, nullable=False)
    
    # Criteria
    cgpa_cutoff = Column(Float, nullable=False, default=6.0)
    allowed_depts = Column(String, nullable=False)  # Comma-separated like "CSE,ECE"
    allowed_backlogs = Column(Integer, nullable=False, default=0)
    bond_details = Column(String, nullable=True)
    selection_process = Column(Text, nullable=True)
    min_attendance = Column(Float, default=75.0)
    batch = Column(String, default="2026", index=True)
    
    interview_date = Column(Date, nullable=False, index=True)
    deadline = Column(Date, nullable=False, index=True)
    status = Column(String, default="DRAFT", index=True)  # DRAFT, PUBLISHED, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Job Description metadata fields
    job_id = Column(String, unique=True, index=True, nullable=True)
    responsibilities = Column(Text, nullable=True)
    required_skills = Column(Text, nullable=True)
    preferred_skills = Column(Text, nullable=True)
    job_type = Column(String, default="Full-Time")
    work_mode = Column(String, default="Onsite")
    openings_count = Column(Integer, default=5)
    hiring_process = Column(Text, nullable=True)
    jd_pdf_path = Column(String, nullable=True)
    company_logo = Column(String, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="drives")
    applications = relationship("Application", back_populates="drive", cascade="all, delete-orphan", passive_deletes=True)
    activities = relationship("PlacementActivity", back_populates="drive", cascade="all, delete-orphan", passive_deletes=True)


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    drive_id = Column(Integer, ForeignKey("placement_drives.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, default="Applied", index=True)  # Applied, Eligible, Shortlisted, Selected, Rejected
    current_round = Column(String, default="Applied")  # Round 1, Round 2, Technical, Coding, HR, Selected, Rejected
    joining_status = Column(String, default="Pending")  # Pending, Accepted, Declined
    remarks = Column(Text, nullable=True)
    applied_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="applications")
    drive = relationship("PlacementDrive", back_populates="applications")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    round_name = Column(String, nullable=False)  # Aptitude, Coding, Technical, HR
    status = Column(String, default="Scheduled", index=True)  # Scheduled, Passed, Failed
    interview_date = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="interviews")
    application = relationship("Application", back_populates="interviews")
    feedbacks = relationship("Feedback", back_populates="interview", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=True, index=True)
    activity_id = Column(Integer, ForeignKey("placement_activities.id", ondelete="CASCADE"), nullable=True, index=True)
    experience_text = Column(Text, nullable=False)
    questions_asked = Column(Text, nullable=True)
    difficulty_rating = Column(Integer, default=3)  # 1 to 5
    preparation_time = Column(String, nullable=True)
    suggestions = Column(Text, nullable=True)
    rating = Column(Integer, default=3)
    theme = Column(String, nullable=True)
    
    # NLP extracted properties
    sentiment_score = Column(Float, default=0.0)  # -1.0 to 1.0
    extracted_keywords = Column(String, nullable=True)  # Comma-separated keywords
    topic_analysis = Column(String, nullable=True)  # Core topic like "DBMS", "DSA"

    # Relationships
    interview = relationship("Interview", back_populates="feedbacks")
    activity = relationship("PlacementActivity", back_populates="feedbacks")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Parent(Base):
    __tablename__ = "parents"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    parent_name = Column(String, nullable=False)
    mobile_number = Column(String, nullable=False, index=True)
    relationship = Column(String, nullable=False)


class ParentOTP(Base):
    __tablename__ = "parent_otps"

    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String, nullable=False, index=True)
    otp_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_requested_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    request_count = Column(Integer, default=0)
    window_start = Column(DateTime, default=datetime.utcnow)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module = Column(String, nullable=False, index=True)
    scope = Column(String, nullable=False)
    scope_value = Column(String, nullable=True)
    action = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    status = Column(String, default="Active", index=True)

    user = relationship("User", backref="user_permissions")


class AccessRequest(Base):
    __tablename__ = "access_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    scope_value = Column(String, nullable=True)
    action = Column(String, nullable=False)
    duration_days = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String, default="Pending", index=True)

    user = relationship("User", backref="user_access_requests")


class CorrectionRequest(Base):
    __tablename__ = "correction_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    field = Column(String, nullable=False)
    current_value = Column(String, nullable=False)
    requested_value = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String, default="Pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", backref="correction_requests")


class PlacementActivity(Base):
    __tablename__ = "placement_activities"

    id = Column(Integer, primary_key=True, index=True)
    placement_drive_id = Column(Integer, ForeignKey("placement_drives.id", ondelete="CASCADE"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    activity_name = Column(String, nullable=False)
    activity_type = Column(String, nullable=False)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    mandatory = Column(Boolean, default=True)

    drive = relationship("PlacementDrive", back_populates="activities")
    company = relationship("Company", backref="activities")
    feedbacks = relationship("Feedback", back_populates="activity", cascade="all, delete-orphan")


class ActivityAttendance(Base):
    __tablename__ = "activity_attendance"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("placement_activities.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    remarks = Column(Text, nullable=True)

    activity = relationship("PlacementActivity", backref="attendance_records")
    student = relationship("Student", backref="activity_attendances")


class Grievance(Base):
    __tablename__ = "grievances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="OPEN", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolution_remarks = Column(Text, nullable=True)

    student = relationship("Student", backref="grievances")
