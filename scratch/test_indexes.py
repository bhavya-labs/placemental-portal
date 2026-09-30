import sqlite3
from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa

conn = sqlite3.connect("placement_portal.db")
# test creating indexes directly or with batch_op
cur = conn.cursor()
indexes_to_create = [
    ("feedbacks", "ix_feedbacks_activity_id", ["activity_id"]),
    ("feedbacks", "ix_feedbacks_interview_id", ["interview_id"]),
    ("grievances", "ix_grievances_status", ["status"]),
    ("grievances", "ix_grievances_student_id", ["student_id"]),
    ("interviews", "ix_interviews_application_id", ["application_id"]),
    ("interviews", "ix_interviews_status", ["status"]),
    ("interviews", "ix_interviews_student_id", ["student_id"]),
    ("notifications", "ix_notifications_is_read", ["is_read"]),
    ("notifications", "ix_notifications_user_id", ["user_id"]),
    ("parent_otps", "ix_parent_otps_mobile_number", ["mobile_number"]),
    ("parents", "ix_parents_mobile_number", ["mobile_number"]),
    ("permissions", "ix_permissions_module", ["module"]),
    ("permissions", "ix_permissions_status", ["status"]),
    ("permissions", "ix_permissions_user_id", ["user_id"]),
    ("placement_activities", "ix_placement_activities_company_id", ["company_id"]),
    ("placement_activities", "ix_placement_activities_date", ["date"]),
    ("placement_activities", "ix_placement_activities_placement_drive_id", ["placement_drive_id"]),
    ("placement_drives", "ix_placement_drives_batch", ["batch"]),
    ("placement_drives", "ix_placement_drives_company_id", ["company_id"]),
    ("placement_drives", "ix_placement_drives_deadline", ["deadline"]),
    ("placement_drives", "ix_placement_drives_interview_date", ["interview_date"]),
    ("placement_drives", "ix_placement_drives_status", ["status"]),
    ("students", "ix_students_batch", ["batch"]),
    ("students", "ix_students_cgpa", ["cgpa"]),
    ("students", "ix_students_dept_id", ["dept_id"]),
    ("students", "ix_students_status", ["status"]),
    ("students", "ix_students_verification_status", ["verification_status"]),
    ("system_logs", "ix_system_logs_action", ["action"]),
    ("system_logs", "ix_system_logs_user_email", ["user_email"]),
    ("users", "ix_users_role", ["role"])
]

for table, idx_name, cols in indexes_to_create:
    col_str = ", ".join(cols)
    sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({col_str})"
    print(f"Executing: {sql}")
    cur.execute(sql)

conn.commit()
print("All indexes created successfully!")
