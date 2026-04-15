# -*- coding: utf-8 -*-
"""作答记录：允许同一场次多次作答（移除 uq_session_user_attempt）。"""

from typing import Sequence, Union

from alembic import op

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_session_user_attempt", "exam_attempt", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("uq_session_user_attempt", "exam_attempt", ["session_id", "user_id"])

