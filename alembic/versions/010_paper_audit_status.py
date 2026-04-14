# -*- coding: utf-8 -*-
"""试卷审核状态：draft 草稿 / reviewed 已审核。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exam_paper",
        sa.Column(
            "audit_status",
            sa.String(length=16),
            nullable=False,
            server_default="draft",
            comment="审核状态：draft 草稿，reviewed 已审核",
        ),
    )
    op.create_index("ix_exam_paper_audit_status", "exam_paper", ["audit_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_exam_paper_audit_status", table_name="exam_paper")
    op.drop_column("exam_paper", "audit_status")
