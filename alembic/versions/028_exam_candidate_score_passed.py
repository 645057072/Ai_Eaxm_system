# -*- coding: utf-8 -*-
"""考生管理：增加得分与是否及格（交卷自动写入）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exam_candidate",
        sa.Column("score", sa.Numeric(10, 2), nullable=True, comment="最近一次交卷得分"),
    )
    op.add_column(
        "exam_candidate",
        sa.Column("passed", sa.Boolean(), nullable=True, comment="最近一次交卷是否及格"),
    )


def downgrade() -> None:
    op.drop_column("exam_candidate", "passed")
    op.drop_column("exam_candidate", "score")

