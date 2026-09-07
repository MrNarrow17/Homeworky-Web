"""Added staff field to homework

Revision ID: 8f68dca786f0
Revises: ...
Create Date: 2026-09-07 22:01:51.349899

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f68dca786f0"
down_revision: Union[str, Sequence[str], None] = "..."
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema using batch mode for SQLite compatibility."""
    with op.batch_alter_table("homework") as batch_op:
        batch_op.add_column(
            sa.Column("staff_id_db", sa.Integer(), nullable=False, server_default="1")
        )
        batch_op.create_index(
            batch_op.f("ix_homework_staff_id_db"), ["staff_id_db"], unique=False
        )
        batch_op.create_foreign_key(
            "fk_homework_staff", "staff", ["staff_id_db"], ["id"]
        )
        batch_op.drop_column("created_by")


def downgrade() -> None:
    """Downgrade schema using batch mode for SQLite compatibility."""
    with op.batch_alter_table("homework") as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_by",
                sa.VARCHAR(),
                autoincrement=False,
                nullable=False,
                server_default="",
            )
        )

        batch_op.drop_constraint("fk_homework_staff", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_homework_staff_id_db"))
        batch_op.drop_column("staff_id_db")
