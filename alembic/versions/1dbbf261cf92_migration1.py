"""migration1

Revision ID: 1dbbf261cf92
Revises: d8f1c4202fee
Create Date: 2026-08-30 21:07:32.958441

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

revision: str = "1dbbf261cf92"
down_revision: Union[str, Sequence[str], None] = "d8f1c4202fee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create the many-to-many table (idempotent)
    op.create_table(
        "staffclasslink",
        sa.Column("staff_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["class.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["staff_id"], ["staff.id"]),
        sa.PrimaryKeyConstraint("staff_id", "class_id"),
        if_not_exists=True,  # safe to run multiple times
    )
    op.create_index(
        op.f("ix_staffclasslink_class_id"),
        "staffclasslink",
        ["class_id"],
        unique=False,
        if_not_exists=True,
    )

    # 2. Drop the old index from staff (outside batch, supports if_exists)
    op.drop_index("ix_staff_class_id_db", table_name="staff", if_exists=True)

    # 3. Drop the old column using batch mode (only if it exists)
    with op.batch_alter_table("staff") as batch_op:
        # Check if column exists using PRAGMA
        conn = op.get_bind()
        columns = conn.execute(text("PRAGMA table_info('staff')")).fetchall()
        if any(col[1] == "class_id_db" for col in columns):
            batch_op.drop_column("class_id_db")


def downgrade() -> None:
    # 1. Re-add the column and foreign key using batch mode
    with op.batch_alter_table("staff") as batch_op:
        conn = op.get_bind()
        columns = conn.execute(text("PRAGMA table_info('staff')")).fetchall()
        if not any(col[1] == "class_id_db" for col in columns):
            batch_op.add_column(sa.Column("class_id_db", sa.INTEGER(), nullable=True))
        # Recreate foreign key (if it doesn't exist, but it's safe to run)
        batch_op.create_foreign_key(
            "fk_staff_class_id_db",  # choose a name
            "class",
            ["class_id_db"],
            ["id"],
            ondelete="CASCADE",
        )

    # 2. Recreate the index (outside batch, supports if_not_exists)
    op.create_index(
        "ix_staff_class_id_db",
        "staff",
        ["class_id_db"],
        unique=False,
        if_not_exists=True,
    )

    # 3. Drop the many-to-many table (idempotent)
    op.drop_index(
        op.f("ix_staffclasslink_class_id"), table_name="staffclasslink", if_exists=True
    )
    op.drop_table("staffclasslink", if_exists=True)
