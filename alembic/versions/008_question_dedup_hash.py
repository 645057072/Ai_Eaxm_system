# -*- coding: utf-8 -*-
"""题目去重指纹 dedup_hash（企业+课程+内容）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("qb_question", sa.Column("dedup_hash", sa.String(64), nullable=True))
    op.create_index(
        "uq_qb_question_ent_course_dedup",
        "qb_question",
        ["enterprise_id", "course_id", "dedup_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_qb_question_ent_course_dedup", table_name="qb_question")
    op.drop_column("qb_question", "dedup_hash")
