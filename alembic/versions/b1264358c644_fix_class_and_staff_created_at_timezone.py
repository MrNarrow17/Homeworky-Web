"""fix class and staff created_at timezone

Revision ID: b1264358c644
Revises: 25534e7549e5
Create Date: 2026-09-02 13:12:57.333235

"""

from typing import Sequence, Union

from alembic import op

# keep whatever revision/down_revision alembic generated for you
revision: str = "..."
down_revision: Union[str, Sequence[str], None] = "25534e7549e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("""
            ALTER TABLE class
            ALTER COLUMN created_at
            TYPE TIMESTAMP WITH TIME ZONE
            USING created_at AT TIME ZONE 'UTC'
        """)
        op.execute("""
            ALTER TABLE staff
            ALTER COLUMN created_at
            TYPE TIMESTAMP WITH TIME ZONE
            USING created_at AT TIME ZONE 'UTC'
        """)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("""
            ALTER TABLE class
            ALTER COLUMN created_at
            TYPE TIMESTAMP WITHOUT TIME ZONE
            USING created_at AT TIME ZONE 'UTC'
        """)
        op.execute("""
            ALTER TABLE staff
            ALTER COLUMN created_at
            TYPE TIMESTAMP WITHOUT TIME ZONE
            USING created_at AT TIME ZONE 'UTC'
        """)
