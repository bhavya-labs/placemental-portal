"""allow_null_interview_id_on_feedback

Revision ID: ac9fcc9ba19f
Revises: 6e105b4276ae
Create Date: 2026-09-06 21:38:49.029551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac9fcc9ba19f'
down_revision: Union[str, Sequence[str], None] = '6e105b4276ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to allow NULL on feedbacks.interview_id for activity feedbacks."""
    with op.batch_alter_table("feedbacks") as batch_op:
        batch_op.alter_column(
            "interview_id",
            existing_type=sa.Integer(),
            nullable=True
        )


def downgrade() -> None:
    """Downgrade schema to revert feedbacks.interview_id to NOT NULL."""
    with op.batch_alter_table("feedbacks") as batch_op:
        batch_op.alter_column(
            "interview_id",
            existing_type=sa.Integer(),
            nullable=False
        )
