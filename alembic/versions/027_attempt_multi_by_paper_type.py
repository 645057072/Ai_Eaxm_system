# -*- coding: utf-8 -*-
"""作答记录：允许同一场次多次作答（移除 uq_session_user_attempt）。"""

from typing import Sequence, Union

from alembic import op

from app.db.migrate_compat import has_unique

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if has_unique("exam_attempt", "uq_session_user_attempt"):
        try:
            op.drop_constraint("uq_session_user_attempt", "exam_attempt", type_="unique")
        except Exception:
            pass


def downgrade() -> None:
    if not has_unique("exam_attempt", "uq_session_user_attempt"):
        try:
            op.create_unique_constraint("uq_session_user_attempt", "exam_attempt", ["session_id", "user_id"])
        except Exception:
            pass

