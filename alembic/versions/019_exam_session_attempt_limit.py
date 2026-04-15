# -*- coding: utf-8 -*-
"""考试场次：答题次数上限（练习卷不限制）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = insp.get_columns(table)
    return any((c.get("name") == col) for c in cols)


def upgrade() -> None:
    if not _has_column("exam_session", "attempt_limit"):
        op.add_column(
            "exam_session",
            sa.Column(
                "attempt_limit",
                sa.Integer(),
                nullable=True,
                comment="答题次数上限；空=不限制（练习卷）",
            ),
        )


def downgrade() -> None:
    if _has_column("exam_session", "attempt_limit"):
        op.drop_column("exam_session", "attempt_limit")
