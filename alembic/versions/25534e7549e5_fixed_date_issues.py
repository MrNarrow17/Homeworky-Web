"""Fixed date issues

Revision ID: 25534e7549e5
Revises: 7c251fe63a1c
Create Date: 2026-09-02 11:52:29.608479
"""

from typing import Sequence, Union

from alembic import op

revision: str = "25534e7549e5"
down_revision: Union[str, Sequence[str], None] = "7c251fe63a1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE homework
        ALTER COLUMN created_at
        TYPE TIMESTAMP WITH TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE homework
        ALTER COLUMN created_at
        TYPE TIMESTAMP WITHOUT TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
    """)
