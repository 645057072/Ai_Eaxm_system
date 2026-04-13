# -*- coding: utf-8 -*-
"""题目题号 question_no（企业-课程-题型-序号）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("qb_question", sa.Column("question_no", sa.String(64), nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE qb_question SET question_no = CONCAT('MIG-', id) WHERE question_no IS NULL"))
    op.alter_column("qb_question", "question_no", existing_type=sa.String(64), nullable=False)
    op.create_index("ix_qb_question_question_no", "qb_question", ["question_no"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_qb_question_question_no", table_name="qb_question")
    op.drop_column("qb_question", "question_no")
