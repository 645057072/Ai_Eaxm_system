# -*- coding: utf-8 -*-
"""考试场次：记录发布人。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = insp.get_columns(table)
    return any((c.get("name") == col) for c in cols)


def upgrade() -> None:
    if not _has_column("exam_session", "published_by"):
        op.add_column(
            "exam_session",
            sa.Column(
                "published_by",
                sa.Integer(),
                nullable=True,
                comment="发布人用户ID",
            ),
        )
        op.create_foreign_key(
            "fk_exam_session_published_by_user",
            "exam_session",
            "sys_user",
            ["published_by"],
            ["id"],
        )
        op.create_index("ix_exam_session_published_by", "exam_session", ["published_by"])


def downgrade() -> None:
    if _has_column("exam_session", "published_by"):
        op.drop_index("ix_exam_session_published_by", table_name="exam_session")
        op.drop_constraint("fk_exam_session_published_by_user", "exam_session", type_="foreignkey")
        op.drop_column("exam_session", "published_by")
