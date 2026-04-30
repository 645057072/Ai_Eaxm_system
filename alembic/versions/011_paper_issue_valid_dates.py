# -*- coding: utf-8 -*-
"""试卷创建日期、有效期（到期后不可再发布引用场次）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.migrate_compat import has_column

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not has_column("exam_paper", "issue_date"):
        op.add_column(
            "exam_paper",
            sa.Column("issue_date", sa.Date(), nullable=True, comment="创建/签发日期"),
        )
    if not has_column("exam_paper", "valid_until"):
        op.add_column(
            "exam_paper",
            sa.Column("valid_until", sa.Date(), nullable=True, comment="有效期至（到期后不可发布引用）"),
        )


def downgrade() -> None:
    if has_column("exam_paper", "valid_until"):
        op.drop_column("exam_paper", "valid_until")
    if has_column("exam_paper", "issue_date"):
        op.drop_column("exam_paper", "issue_date")
