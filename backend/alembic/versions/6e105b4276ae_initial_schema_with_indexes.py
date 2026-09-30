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


def upgrade() -> None:
    """Upgrade schema by ensuring ORM tables exist and adding missing indexes cleanly across SQLite and PostgreSQL."""
    conn = op.get_bind()
    
    # Ensure all ORM tables exist before applying indexes (critical for fresh clone installs)
    from backend.app.models import Base
    Base.metadata.create_all(bind=conn)

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
