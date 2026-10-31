"""add_reference_key_to_notifications

Revision ID: b7e21c8340d1
Revises: ac9fcc9ba19f
Create Date: 2026-10-31 20:28:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e21c8340d1'
down_revision: Union[str, Sequence[str], None] = 'ac9fcc9ba19f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable reference_key column and index to notifications table for broadcast deduplication."""
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"

    if is_sqlite:
        op.execute("ALTER TABLE notifications ADD COLUMN reference_key VARCHAR;")
        op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_reference_key ON notifications (reference_key);")
    else:
        op.add_column("notifications", sa.Column("reference_key", sa.String(), nullable=True))
        op.create_index("ix_notifications_reference_key", "notifications", ["reference_key"])


def downgrade() -> None:
    """Drop reference_key column and index."""
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"

    if is_sqlite:
        op.execute("DROP INDEX IF EXISTS ix_notifications_reference_key;")
    else:
        op.drop_index("ix_notifications_reference_key", table_name="notifications")
        op.drop_column("notifications", "reference_key")
