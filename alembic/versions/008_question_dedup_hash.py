# -*- coding: utf-8 -*-
"""题目去重指纹 dedup_hash（企业+课程+内容）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "008"
down_revision: Union[str, None] = "007"
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


def upgrade() -> None:
    # 幂等：历史库可能已存在 dedup_hash 字段/索引
    if not _has_column("qb_question", "dedup_hash"):
        op.add_column("qb_question", sa.Column("dedup_hash", sa.String(64), nullable=True))
    if not _has_index("qb_question", "uq_qb_question_ent_course_dedup"):
        try:
            op.create_index(
                "uq_qb_question_ent_course_dedup",
                "qb_question",
                ["enterprise_id", "course_id", "dedup_hash"],
                unique=True,
            )
        except Exception:
            pass


def downgrade() -> None:
    if _has_index("qb_question", "uq_qb_question_ent_course_dedup"):
        op.drop_index("uq_qb_question_ent_course_dedup", table_name="qb_question")
    if _has_column("qb_question", "dedup_hash"):
        op.drop_column("qb_question", "dedup_hash")
