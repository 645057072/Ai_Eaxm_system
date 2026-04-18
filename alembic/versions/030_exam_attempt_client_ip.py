# -*- coding: utf-8 -*-
"""作答记录：客户端 IP（大屏地理热力与审计）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exam_attempt",
        sa.Column(
            "client_ip",
            sa.String(45),
            nullable=True,
            comment="客户端 IP（进入考试时记录，用于数智大屏地域分布）",
        ),
    )


def downgrade() -> None:
    op.drop_column("exam_attempt", "client_ip")
