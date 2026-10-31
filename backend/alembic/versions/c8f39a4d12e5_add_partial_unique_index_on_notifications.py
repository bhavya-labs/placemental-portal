"""add_partial_unique_index_on_notifications

Revision ID: c8f39a4d12e5
Revises: b7e21c8340d1
Create Date: 2026-10-31 21:12:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c8f39a4d12e5'
down_revision: Union[str, Sequence[str], None] = 'b7e21c8340d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add partial unique index on notifications (user_id, reference_key)
    where reference_key is NOT NULL to prevent concurrent duplicate broadcasts.
    Compatible with both SQLite (>= 3.8.0) and PostgreSQL.
    """
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_notif_user_ref "
        "ON notifications (user_id, reference_key) "
        "WHERE reference_key IS NOT NULL;"
    )


def downgrade() -> None:
    """Drop partial unique index uq_notif_user_ref."""
    op.execute("DROP INDEX IF EXISTS uq_notif_user_ref;")
