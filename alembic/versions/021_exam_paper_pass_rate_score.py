# -*- coding: utf-8 -*-
"""试卷：及格率、及格分（合格分由总分×及格率/100 自动计算）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.migrate_compat import has_column

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not has_column("exam_paper", "pass_rate"):
        op.add_column(
            "exam_paper",
            sa.Column(
                "pass_rate",
                sa.Numeric(5, 2),
                nullable=False,
                server_default="60.00",
                comment="及格率(%)，合格分=总分×及格率/100",
            ),
        )
    if not has_column("exam_paper", "pass_score"):
        op.add_column(
            "exam_paper",
            sa.Column(
                "pass_score",
                sa.Numeric(10, 2),
                nullable=False,
                server_default="0.00",
                comment="及格分(合格分)，由总分与及格率自动计算",
            ),
        )
    # 按当前总分回填及格分
    op.execute(
        sa.text(
            "UPDATE exam_paper SET pass_score = ROUND(total_score * pass_rate / 100, 2)"
        )
    )


def downgrade() -> None:
    if has_column("exam_paper", "pass_score"):
        op.drop_column("exam_paper", "pass_score")
    if has_column("exam_paper", "pass_rate"):
        op.drop_column("exam_paper", "pass_rate")
