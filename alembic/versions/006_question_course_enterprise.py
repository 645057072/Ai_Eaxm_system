# -*- coding: utf-8 -*-
"""题目关联课程、所属企业（题库导入）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        cols = insp.get_columns(table) or []
        return any((c.get("name") == col) for c in cols)
    except Exception:
        return False


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        idx = insp.get_indexes(table) or []
        return any((i.get("name") == index_name) for i in idx)
    except Exception:
        return False


def _has_fk(table: str, fk_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        fks = insp.get_foreign_keys(table) or []
        return any((fk.get("name") == fk_name) for fk in fks)
    except Exception:
        return False


def upgrade() -> None:
    # 幂等：历史库可能已存在字段/索引/外键（避免重复执行报错）
    if not _has_column("qb_question", "course_id"):
        op.add_column("qb_question", sa.Column("course_id", sa.Integer(), nullable=True))
    if not _has_column("qb_question", "enterprise_id"):
        op.add_column("qb_question", sa.Column("enterprise_id", sa.Integer(), nullable=True))
    if not _has_fk("qb_question", "fk_qb_question_course"):
        try:
            op.create_foreign_key("fk_qb_question_course", "qb_question", "sys_course", ["course_id"], ["id"])
        except Exception:
            pass
    if not _has_fk("qb_question", "fk_qb_question_enterprise"):
        try:
            op.create_foreign_key(
                "fk_qb_question_enterprise", "qb_question", "sys_enterprise", ["enterprise_id"], ["id"]
            )
        except Exception:
            pass
    if not _has_index("qb_question", "ix_qb_question_course_id"):
        try:
            op.create_index("ix_qb_question_course_id", "qb_question", ["course_id"], unique=False)
        except Exception:
            pass
    if not _has_index("qb_question", "ix_qb_question_enterprise_id"):
        try:
            op.create_index("ix_qb_question_enterprise_id", "qb_question", ["enterprise_id"], unique=False)
        except Exception:
            pass


def downgrade() -> None:
    if _has_index("qb_question", "ix_qb_question_enterprise_id"):
        op.drop_index("ix_qb_question_enterprise_id", table_name="qb_question")
    if _has_index("qb_question", "ix_qb_question_course_id"):
        op.drop_index("ix_qb_question_course_id", table_name="qb_question")
    try:
        op.drop_constraint("fk_qb_question_enterprise", "qb_question", type_="foreignkey")
    except Exception:
        pass
    try:
        op.drop_constraint("fk_qb_question_course", "qb_question", type_="foreignkey")
    except Exception:
        pass
    if _has_column("qb_question", "enterprise_id"):
        op.drop_column("qb_question", "enterprise_id")
    if _has_column("qb_question", "course_id"):
        op.drop_column("qb_question", "course_id")
