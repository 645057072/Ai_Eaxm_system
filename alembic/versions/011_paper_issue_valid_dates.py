# -*- coding: utf-8 -*-
"""试卷创建日期、有效期（到期后不可再发布引用场次）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exam_paper",
        sa.Column("issue_date", sa.Date(), nullable=True, comment="创建/签发日期"),
    )
    op.add_column(
        "exam_paper",
        sa.Column("valid_until", sa.Date(), nullable=True, comment="有效期至（到期后不可发布引用）"),
    )


def downgrade() -> None:
    op.drop_column("exam_paper", "valid_until")
    op.drop_column("exam_paper", "issue_date")
