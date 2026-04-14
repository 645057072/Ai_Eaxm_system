# -*- coding: utf-8 -*-
"""用户：关联学员、启用日期、失效日期。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sys_user",
        sa.Column("student_id", sa.Integer(), nullable=True, comment="关联学员ID"),
    )
    op.create_foreign_key(
        "fk_sys_user_student_id",
        "sys_user",
        "student",
        ["student_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint("uq_sys_user_student_id", "sys_user", ["student_id"])

    op.add_column(
        "sys_user",
        sa.Column("enable_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE"), comment="启用日期"),
    )
    op.add_column(
        "sys_user",
        sa.Column("expire_date", sa.Date(), nullable=True, comment="失效日期"),
    )


def downgrade() -> None:
    op.drop_column("sys_user", "expire_date")
    op.drop_column("sys_user", "enable_date")
    op.drop_constraint("uq_sys_user_student_id", "sys_user", type_="unique")
    op.drop_constraint("fk_sys_user_student_id", "sys_user", type_="foreignkey")
    op.drop_column("sys_user", "student_id")

