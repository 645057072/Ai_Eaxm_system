# -*- coding: utf-8 -*-
"""题目题号 question_no（企业-课程-题型-序号）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "007"
down_revision: Union[str, None] = "006"
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
    # 幂等：历史库可能已存在 question_no 字段
    if not _has_column("qb_question", "question_no"):
        op.add_column("qb_question", sa.Column("question_no", sa.String(64), nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE qb_question SET question_no = CONCAT('MIG-', id) WHERE question_no IS NULL"))
    try:
        op.alter_column("qb_question", "question_no", existing_type=sa.String(64), nullable=False)
    except Exception:
        # 兼容：部分环境下已为 NOT NULL
        pass
    if not _has_index("qb_question", "ix_qb_question_question_no"):
        try:
            op.create_index("ix_qb_question_question_no", "qb_question", ["question_no"], unique=True)
        except Exception:
            pass


def downgrade() -> None:
    if _has_index("qb_question", "ix_qb_question_question_no"):
        op.drop_index("ix_qb_question_question_no", table_name="qb_question")
    if _has_column("qb_question", "question_no"):
        op.drop_column("qb_question", "question_no")
