# -*- coding: utf-8 -*-
"""练习卷交卷报告：exam_attempt.practice_report。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.migrate_compat import has_column

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not has_column("exam_attempt", "practice_report"):
        op.add_column(
            "exam_attempt",
            sa.Column("practice_report", sa.Text(), nullable=True, comment="练习卷交卷后生成的文字报告（约一页A4五号字）"),
        )


def downgrade() -> None:
    if has_column("exam_attempt", "practice_report"):
        op.drop_column("exam_attempt", "practice_report")
