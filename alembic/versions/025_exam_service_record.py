# -*- coding: utf-8 -*-
"""考试服务记录表：交卷自动生成。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exam_service_record",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False, comment="对应作答记录"),
        sa.Column("enterprise_id", sa.Integer(), nullable=False, comment="所属企业"),
        sa.Column("exam_no", sa.String(length=64), nullable=False, comment="考试编号（场次编码）"),
        sa.Column("course_name", sa.String(length=200), nullable=False, server_default="", comment="课程名称快照"),
        sa.Column("paper_title", sa.String(length=200), nullable=False, server_default="", comment="试卷名称快照"),
        sa.Column("enterprise_name", sa.String(length=200), nullable=False, server_default="", comment="企业名称快照"),
        sa.Column("student_display", sa.String(length=200), nullable=False, server_default="", comment="学员展示"),
        sa.Column("score", sa.Numeric(10, 2), nullable=False, server_default="0", comment="得分"),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.text("0"), comment="是否通过"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["attempt_id"], ["exam_attempt.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["enterprise_id"], ["sys_enterprise.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", name="uq_exam_service_record_attempt"),
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_exam_service_record_enterprise_id", "exam_service_record", ["enterprise_id"], unique=False)
    op.create_index("ix_exam_service_record_exam_no", "exam_service_record", ["exam_no"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_exam_service_record_exam_no", table_name="exam_service_record")
    op.drop_index("ix_exam_service_record_enterprise_id", table_name="exam_service_record")
    op.drop_table("exam_service_record")
