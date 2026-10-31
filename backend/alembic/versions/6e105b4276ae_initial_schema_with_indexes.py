"""initial_schema_with_indexes

Revision ID: 6e105b4276ae
Revises: 
Create Date: 2026-09-05 22:39:45.599493

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e105b4276ae'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = [
    # Table, Index Name, Columns
    ("users", "ix_users_role", ["role"]),
    ("students", "ix_students_dept_id", ["dept_id"]),
    ("students", "ix_students_batch", ["batch"]),
    ("students", "ix_students_cgpa", ["cgpa"]),
    ("students", "ix_students_status", ["status"]),
    ("students", "ix_students_verification_status", ["verification_status"]),
    ("faculty", "ix_faculty_dept_id", ["dept_id"]),
    ("placement_drives", "ix_placement_drives_company_id", ["company_id"]),
    ("placement_drives", "ix_placement_drives_batch", ["batch"]),
    ("placement_drives", "ix_placement_drives_status", ["status"]),
    ("placement_drives", "ix_placement_drives_interview_date", ["interview_date"]),
    ("placement_drives", "ix_placement_drives_deadline", ["deadline"]),
    ("applications", "ix_applications_student_id", ["student_id"]),
    ("applications", "ix_applications_drive_id", ["drive_id"]),
    ("applications", "ix_applications_status", ["status"]),
    ("interviews", "ix_interviews_student_id", ["student_id"]),
    ("interviews", "ix_interviews_application_id", ["application_id"]),
    ("interviews", "ix_interviews_status", ["status"]),
    ("feedbacks", "ix_feedbacks_interview_id", ["interview_id"]),
    ("feedbacks", "ix_feedbacks_activity_id", ["activity_id"]),
    ("notifications", "ix_notifications_user_id", ["user_id"]),
    ("notifications", "ix_notifications_is_read", ["is_read"]),
    ("system_logs", "ix_system_logs_user_email", ["user_email"]),
    ("system_logs", "ix_system_logs_action", ["action"]),
    ("parents", "ix_parents_student_id", ["student_id"]),
    ("parents", "ix_parents_mobile_number", ["mobile_number"]),
    ("parent_otps", "ix_parent_otps_mobile_number", ["mobile_number"]),
    ("permissions", "ix_permissions_user_id", ["user_id"]),
    ("permissions", "ix_permissions_module", ["module"]),
    ("permissions", "ix_permissions_status", ["status"]),
    ("access_requests", "ix_access_requests_user_id", ["user_id"]),
    ("access_requests", "ix_access_requests_status", ["status"]),
    ("correction_requests", "ix_correction_requests_student_id", ["student_id"]),
    ("correction_requests", "ix_correction_requests_status", ["status"]),
    ("placement_activities", "ix_placement_activities_company_id", ["company_id"]),
    ("placement_activities", "ix_placement_activities_placement_drive_id", ["placement_drive_id"]),
    ("placement_activities", "ix_placement_activities_date", ["date"]),
    ("activity_attendance", "ix_activity_attendance_activity_id", ["activity_id"]),
    ("activity_attendance", "ix_activity_attendance_student_id", ["student_id"]),
    ("activity_attendance", "ix_activity_attendance_status", ["status"]),
    ("grievances", "ix_grievances_student_id", ["student_id"]),
    ("grievances", "ix_grievances_status", ["status"]),
]


def _create_initial_tables(conn) -> None:
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if "departments" not in existing_tables:
        op.create_table(
            "departments",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(), unique=True, nullable=False),
            sa.Column("code", sa.String(), unique=True, nullable=False),
        )

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("email", sa.String(), unique=True, nullable=False),
            sa.Column("password_hash", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    if "students" not in existing_tables:
        op.create_table(
            "students",
            sa.Column("id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("dept_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
            sa.Column("gender", sa.String(), nullable=False),
            sa.Column("batch", sa.String(), nullable=False),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("cgpa", sa.Float(), nullable=False, default=0.0),
            sa.Column("attendance", sa.Float(), nullable=False, default=0.0),
            sa.Column("backlogs", sa.Integer(), nullable=False, default=0),
            sa.Column("sgpa_sem1", sa.Float(), nullable=True),
            sa.Column("sgpa_sem2", sa.Float(), nullable=True),
            sa.Column("sgpa_sem3", sa.Float(), nullable=True),
            sa.Column("sgpa_sem4", sa.Float(), nullable=True),
            sa.Column("sgpa_sem5", sa.Float(), nullable=True),
            sa.Column("sgpa_sem6", sa.Float(), nullable=True),
            sa.Column("sgpa_sem7", sa.Float(), nullable=True),
            sa.Column("sgpa_sem8", sa.Float(), nullable=True),
            sa.Column("skills", sa.Text(), nullable=True),
            sa.Column("projects", sa.Text(), nullable=True),
            sa.Column("internships", sa.Text(), nullable=True),
            sa.Column("certifications", sa.Text(), nullable=True),
            sa.Column("resume_path", sa.String(), nullable=True),
            sa.Column("github_url", sa.String(), nullable=True),
            sa.Column("linkedin_url", sa.String(), nullable=True),
            sa.Column("leetcode_score", sa.Integer(), nullable=True, default=0),
            sa.Column("codechef_score", sa.Integer(), nullable=True, default=0),
            sa.Column("hackerrank_score", sa.Integer(), nullable=True, default=0),
            sa.Column("readiness_score", sa.Float(), nullable=True, default=0.0),
            sa.Column("placement_probability", sa.Float(), nullable=True, default=0.0),
            sa.Column("ai_recommendations", sa.Text(), nullable=True),
            sa.Column("status", sa.String(), nullable=True, default="Unplaced"),
            sa.Column("profile_completed", sa.Boolean(), nullable=True, default=False),
            sa.Column("resume_text", sa.Text(), nullable=True),
            sa.Column("resume_ats_score", sa.Integer(), nullable=True, default=0),
            sa.Column("resume_analysis_json", sa.Text(), nullable=True),
            sa.Column("verification_status", sa.String(), nullable=True, default="VERIFIED"),
            sa.Column("section", sa.String(), nullable=True, default="A"),
            sa.Column("portfolio_url", sa.Text(), nullable=True),
            sa.Column("career_preferences", sa.Text(), nullable=True),
        )

    if "faculty" not in existing_tables:
        op.create_table(
            "faculty",
            sa.Column("id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("dept_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
            sa.Column("designation", sa.String(), nullable=False),
        )

    if "companies" not in existing_tables:
        op.create_table(
            "companies",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(), unique=True, nullable=False),
            sa.Column("industry", sa.String(), nullable=False),
            sa.Column("website", sa.String(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
        )

    if "placement_drives" not in existing_tables:
        op.create_table(
            "placement_drives",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("package_lpa", sa.Float(), nullable=False),
            sa.Column("location", sa.String(), nullable=False),
            sa.Column("cgpa_cutoff", sa.Float(), nullable=False, default=6.0),
            sa.Column("allowed_depts", sa.String(), nullable=False),
            sa.Column("allowed_backlogs", sa.Integer(), nullable=False, default=0),
            sa.Column("bond_details", sa.String(), nullable=True),
            sa.Column("selection_process", sa.Text(), nullable=True),
            sa.Column("interview_date", sa.Date(), nullable=False),
            sa.Column("deadline", sa.Date(), nullable=False),
            sa.Column("status", sa.String(), nullable=True, default="DRAFT"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("job_id", sa.String(), unique=True, nullable=True),
            sa.Column("responsibilities", sa.Text(), nullable=True),
            sa.Column("required_skills", sa.Text(), nullable=True),
            sa.Column("preferred_skills", sa.Text(), nullable=True),
            sa.Column("job_type", sa.String(), nullable=True, default="Full-Time"),
            sa.Column("work_mode", sa.String(), nullable=True, default="Onsite"),
            sa.Column("openings_count", sa.Integer(), nullable=True, default=5),
            sa.Column("hiring_process", sa.Text(), nullable=True),
            sa.Column("jd_pdf_path", sa.String(), nullable=True),
            sa.Column("company_logo", sa.String(), nullable=True),
            sa.Column("min_attendance", sa.Float(), nullable=True, default=75.0),
            sa.Column("batch", sa.String(), nullable=True, default="2026"),
        )

    if "applications" not in existing_tables:
        op.create_table(
            "applications",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drive_id", sa.Integer(), sa.ForeignKey("placement_drives.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(), nullable=True, default="Applied"),
            sa.Column("current_round", sa.String(), nullable=True, default="Applied"),
            sa.Column("joining_status", sa.String(), nullable=True, default="Pending"),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("applied_date", sa.DateTime(), nullable=True),
        )

    if "interviews" not in existing_tables:
        op.create_table(
            "interviews",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
            sa.Column("round_name", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=True, default="Scheduled"),
            sa.Column("interview_date", sa.DateTime(), nullable=True),
            sa.Column("remarks", sa.Text(), nullable=True),
        )

    if "placement_activities" not in existing_tables:
        op.create_table(
            "placement_activities",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("placement_drive_id", sa.Integer(), sa.ForeignKey("placement_drives.id", ondelete="CASCADE"), nullable=True),
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
            sa.Column("activity_name", sa.String(), nullable=False),
            sa.Column("activity_type", sa.String(), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("start_time", sa.String(), nullable=False),
            sa.Column("end_time", sa.String(), nullable=False),
            sa.Column("location", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("mandatory", sa.Boolean(), nullable=True, default=True),
        )

    if "feedbacks" not in existing_tables:
        # Schema at 6e105b4276ae had interview_id NOT NULL (relaxed to nullable in ac9fcc9ba19f)
        op.create_table(
            "feedbacks",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("interview_id", sa.Integer(), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False),
            sa.Column("activity_id", sa.Integer(), sa.ForeignKey("placement_activities.id"), nullable=True),
            sa.Column("experience_text", sa.Text(), nullable=False),
            sa.Column("questions_asked", sa.Text(), nullable=True),
            sa.Column("difficulty_rating", sa.Integer(), nullable=True, default=3),
            sa.Column("preparation_time", sa.String(), nullable=True),
            sa.Column("suggestions", sa.Text(), nullable=True),
            sa.Column("sentiment_score", sa.Float(), nullable=True, default=0.0),
            sa.Column("extracted_keywords", sa.String(), nullable=True),
            sa.Column("topic_analysis", sa.String(), nullable=True),
            sa.Column("rating", sa.Integer(), nullable=True, default=3),
            sa.Column("theme", sa.Text(), nullable=True),
        )

    if "notifications" not in existing_tables:
        # Schema at 6e105b4276ae did NOT include reference_key (added cleanly in b7e21c8340d1)
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("is_read", sa.Boolean(), nullable=True, default=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    if "system_logs" not in existing_tables:
        op.create_table(
            "system_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_email", sa.String(), nullable=False),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    if "parents" not in existing_tables:
        op.create_table(
            "parents",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False),
            sa.Column("parent_name", sa.String(), nullable=False),
            sa.Column("mobile_number", sa.String(), nullable=False),
            sa.Column("relationship", sa.String(), nullable=False),
        )

    if "parent_otps" not in existing_tables:
        op.create_table(
            "parent_otps",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("mobile_number", sa.String(), nullable=False),
            sa.Column("otp_hash", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=True, default=0),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("last_requested_at", sa.DateTime(), nullable=True),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column("request_count", sa.Integer(), nullable=True, default=0),
            sa.Column("window_start", sa.DateTime(), nullable=True),
        )

    if "permissions" not in existing_tables:
        op.create_table(
            "permissions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("module", sa.String(), nullable=False),
            sa.Column("scope", sa.String(), nullable=False),
            sa.Column("scope_value", sa.String(), nullable=True),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("start_date", sa.DateTime(), nullable=False),
            sa.Column("expiry_date", sa.DateTime(), nullable=False),
            sa.Column("status", sa.String(), nullable=True, default="Active"),
        )

    if "access_requests" not in existing_tables:
        op.create_table(
            "access_requests",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("module", sa.String(), nullable=False),
            sa.Column("scope", sa.String(), nullable=False),
            sa.Column("scope_value", sa.String(), nullable=True),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("duration_days", sa.Integer(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("status", sa.String(), nullable=True, default="Pending"),
        )

    if "correction_requests" not in existing_tables:
        op.create_table(
            "correction_requests",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
            sa.Column("field", sa.String(), nullable=False),
            sa.Column("current_value", sa.String(), nullable=False),
            sa.Column("requested_value", sa.String(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("status", sa.String(), nullable=True, default="Pending"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    if "activity_attendance" not in existing_tables:
        op.create_table(
            "activity_attendance",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("activity_id", sa.Integer(), sa.ForeignKey("placement_activities.id", ondelete="CASCADE"), nullable=False),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("remarks", sa.Text(), nullable=True),
        )

    if "grievances" not in existing_tables:
        op.create_table(
            "grievances",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("status", sa.String(), nullable=True, default="OPEN"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("resolution_remarks", sa.Text(), nullable=True),
        )


def upgrade() -> None:
    """Upgrade schema by ensuring initial tables exist and adding missing indexes cleanly across SQLite and PostgreSQL."""
    conn = op.get_bind()
    
    # Create initial frozen tables idempotently
    _create_initial_tables(conn)

    is_sqlite = conn.dialect.name == "sqlite"

    for table, idx_name, cols in INDEXES:
        col_list = ", ".join(cols)
        if is_sqlite:
            op.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({col_list})")
        else:
            try:
                op.create_index(idx_name, table, cols)
            except Exception:
                pass


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"

    for table, idx_name, cols in reversed(INDEXES):
        if is_sqlite:
            op.execute(f"DROP INDEX IF EXISTS {idx_name}")
        else:
            try:
                op.drop_index(idx_name, table_name=table)
            except Exception:
                pass
