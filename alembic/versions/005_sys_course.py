# -*- coding: utf-8 -*-
"""课程信息表 sys_course。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        return insp.has_table(table)
    except Exception:
        return table in (insp.get_table_names() or [])


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        idx = insp.get_indexes(table) or []
        return any((i.get("name") == index_name) for i in idx)
    except Exception:
        return False


def upgrade() -> None:
    # 幂等：历史上可能因迁移中断/手工建表导致 sys_course 已存在
    if not _has_table("sys_course"):
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
    if not _has_index("sys_course", "ix_sys_course_enterprise_id"):
        op.create_index("ix_sys_course_enterprise_id", "sys_course", ["enterprise_id"], unique=False)


def downgrade() -> None:
    if _has_table("sys_course"):
        if _has_index("sys_course", "ix_sys_course_enterprise_id"):
            op.drop_index("ix_sys_course_enterprise_id", table_name="sys_course")
        op.drop_table("sys_course")
