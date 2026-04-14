# -*- coding: utf-8 -*-
"""用户：关联学员、启用日期、失效日期。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = insp.get_columns(table)
    return any((c.get("name") == col) for c in cols)


def _has_fk(table: str, fk_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        fks = insp.get_foreign_keys(table)
    except Exception:
        return False
    return any((fk.get("name") == fk_name) for fk in fks)


def _has_unique(table: str, uq_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    # MySQL 下 unique 可能出现在 get_indexes 或 get_unique_constraints，两个都尝试
    try:
        uqs = insp.get_unique_constraints(table)
        if any((u.get("name") == uq_name) for u in uqs):
            return True
    except Exception:
        pass
    try:
        idx = insp.get_indexes(table)
        return any((i.get("name") == uq_name and i.get("unique")) for i in idx)
    except Exception:
        return False


def upgrade() -> None:
    # 兼容：某些环境已提前存在 student_id（避免重复加列导致迁移失败）
    if not _has_column("sys_user", "student_id"):
        op.add_column(
            "sys_user",
            sa.Column("student_id", sa.Integer(), nullable=True, comment="关联学员ID"),
        )
    if not _has_fk("sys_user", "fk_sys_user_student_id"):
        try:
            op.create_foreign_key(
                "fk_sys_user_student_id",
                "sys_user",
                "student",
                ["student_id"],
                ["id"],
                ondelete="SET NULL",
            )
        except Exception:
            # 兼容：外键可能已存在或目标表不同命名
            pass
    if not _has_unique("sys_user", "uq_sys_user_student_id"):
        try:
            op.create_unique_constraint("uq_sys_user_student_id", "sys_user", ["student_id"])
        except Exception:
            pass

    if not _has_column("sys_user", "enable_date"):
        op.add_column(
            "sys_user",
            sa.Column(
                "enable_date",
                sa.Date(),
                nullable=False,
                server_default=sa.text("CURRENT_DATE"),
                comment="启用日期",
            ),
        )
    if not _has_column("sys_user", "expire_date"):
        op.add_column(
            "sys_user",
            sa.Column("expire_date", sa.Date(), nullable=True, comment="失效日期"),
        )


def downgrade() -> None:
    if _has_column("sys_user", "expire_date"):
        op.drop_column("sys_user", "expire_date")
    if _has_column("sys_user", "enable_date"):
        op.drop_column("sys_user", "enable_date")
    try:
        op.drop_constraint("uq_sys_user_student_id", "sys_user", type_="unique")
    except Exception:
        pass
    try:
        op.drop_constraint("fk_sys_user_student_id", "sys_user", type_="foreignkey")
    except Exception:
        pass
    if _has_column("sys_user", "student_id"):
        op.drop_column("sys_user", "student_id")

