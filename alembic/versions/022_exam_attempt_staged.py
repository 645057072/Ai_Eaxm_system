# -*- coding: utf-8 -*-
"""练习卷暂存：exam_attempt.staged。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exam_attempt",
        sa.Column(
            "staged",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
            comment="练习卷：考生点击暂存后为真，用于再次进入时提示继续作答",
        ),
    )


def downgrade() -> None:
    op.drop_column("exam_attempt", "staged")
