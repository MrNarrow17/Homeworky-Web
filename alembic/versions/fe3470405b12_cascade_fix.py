"""cascade_fix

Revision ID: fe3470405b12
Revises: 675ec1e90f23
Create Date: 2026-08-24 11:17:02.071054

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fe3470405b12"
down_revision: Union[str, Sequence[str], None] = "675ec1e90f23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    if is_sqlite:
        # recreate="always" каже Alembic повністю перебудувати таблицю
        # з новою схемою без спроби знайти старі безназванні constraints
        with op.batch_alter_table("classsession", recreate="always") as batch_op:
            batch_op.create_foreign_key(
                "fk_classsession_class_id_class",
                "class",
                ["class_id"],
                ["id"],
                ondelete="CASCADE",
            )

        with op.batch_alter_table("homework", recreate="always") as batch_op:
            batch_op.create_foreign_key(
                "fk_homework_class_id_class",
                "class",
                ["class_id"],
                ["id"],
                ondelete="CASCADE",
            )

        with op.batch_alter_table("staffmember", recreate="always") as batch_op:
            batch_op.create_foreign_key(
                "fk_staffmember_class_id_class",
                "class",
                ["class_id"],
                ["id"],
                ondelete="CASCADE",
            )

        with op.batch_alter_table("staffsession", recreate="always") as batch_op:
            batch_op.create_foreign_key(
                "fk_staffsession_staff_member_id_staffmember",
                "staffmember",
                ["staff_member_id"],
                ["id"],
                ondelete="CASCADE",
            )
    else:
        # Для PostgreSQL на сервері
        op.drop_constraint(
            "classsession_class_id_fkey", "classsession", type_="foreignkey"
        )
        op.create_foreign_key(
            "classsession_class_id_fkey",
            "classsession",
            "class",
            ["class_id"],
            ["id"],
            ondelete="CASCADE",
        )

        op.drop_constraint("homework_class_id_fkey", "homework", type_="foreignkey")
        op.create_foreign_key(
            "homework_class_id_fkey",
            "homework",
            "class",
            ["class_id"],
            ["id"],
            ondelete="CASCADE",
        )

        op.drop_constraint(
            "staffmember_class_id_fkey", "staffmember", type_="foreignkey"
        )
        op.create_foreign_key(
            "staffmember_class_id_fkey",
            "staffmember",
            "class",
            ["class_id"],
            ["id"],
            ondelete="CASCADE",
        )

        op.drop_constraint(
            "staffsession_staff_member_id_fkey", "staffsession", type_="foreignkey"
        )
        op.create_foreign_key(
            "staffsession_staff_member_id_fkey",
            "staffsession",
            "staffmember",
            ["staff_member_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    if is_sqlite:
        with op.batch_alter_table("staffsession") as batch_op:
            batch_op.create_foreign_key(
                "fk_staffsession_staff_member_id_staffmember",
                "staffmember",
                ["staff_member_id"],
                ["id"],
            )

        with op.batch_alter_table("staffmember") as batch_op:
            batch_op.create_foreign_key(
                "fk_staffmember_class_id_class", "class", ["class_id"], ["id"]
            )

        with op.batch_alter_table("homework") as batch_op:
            batch_op.create_foreign_key(
                "fk_homework_class_id_class", "class", ["class_id"], ["id"]
            )

        with op.batch_alter_table("classsession") as batch_op:
            batch_op.create_foreign_key(
                "fk_classsession_class_id_class", "class", ["class_id"], ["id"]
            )
    else:
        op.drop_constraint(
            "staffsession_staff_member_id_fkey", "staffsession", type_="foreignkey"
        )
        op.create_foreign_key(
            "staffsession_staff_member_id_fkey",
            "staffsession",
            "staffmember",
            ["staff_member_id"],
            ["id"],
        )

        op.drop_constraint(
            "staffmember_class_id_fkey", "staffmember", type_="foreignkey"
        )
        op.create_foreign_key(
            "staffmember_class_id_fkey", "staffmember", "class", ["class_id"], ["id"]
        )

        op.drop_constraint("homework_class_id_fkey", "homework", type_="foreignkey")
        op.create_foreign_key(
            "homework_class_id_fkey", "homework", "class", ["class_id"], ["id"]
        )

        op.drop_constraint(
            "classsession_class_id_fkey", "classsession", type_="foreignkey"
        )
        op.create_foreign_key(
            "classsession_class_id_fkey", "classsession", "class", ["class_id"], ["id"]
        )
