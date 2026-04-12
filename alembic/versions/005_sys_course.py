# -*- coding: utf-8 -*-
"""课程信息表 sys_course。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sys_course",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False, comment="课程名称"),
        sa.Column("instructor", sa.String(length=100), nullable=False, comment="讲师"),
        sa.Column("period_text", sa.String(length=255), nullable=False, comment="课程期间"),
        sa.Column("description", sa.Text(), nullable=True, comment="课程简介"),
        sa.Column("enterprise_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["enterprise_id"], ["sys_enterprise.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["sys_user.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_sys_course_enterprise_id", "sys_course", ["enterprise_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sys_course_enterprise_id", table_name="sys_course")
    op.drop_table("sys_course")
