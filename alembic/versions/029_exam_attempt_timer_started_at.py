# -*- coding: utf-8 -*-
"""作答记录：本次考试倒计时起点（与历史 started_at 区分，用于续考与自动交卷）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exam_attempt",
        sa.Column(
            "exam_timer_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="本次作答考试时长起算时刻（进入考试/续考时写入）",
        ),
    )
    op.execute(
        sa.text(
            "UPDATE exam_attempt SET exam_timer_started_at = started_at "
            "WHERE exam_timer_started_at IS NULL AND started_at IS NOT NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("exam_attempt", "exam_timer_started_at")
