# -*- coding: utf-8 -*-
"""错题集表：exam_wrong_question。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.migrate_compat import has_index, has_table, safe_create_index

revision: str = "026"
down_revision: Union[str, None] = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not has_table("exam_wrong_question"):
        op.create_table(
            "exam_wrong_question",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("enterprise_id", sa.Integer(), nullable=False, comment="所属企业"),
            sa.Column("user_id", sa.Integer(), nullable=False, comment="用户"),
            sa.Column("course_id", sa.Integer(), nullable=False, comment="课程"),
            sa.Column("question_id", sa.Integer(), nullable=False, comment="题目"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["enterprise_id"], ["sys_enterprise.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["course_id"], ["sys_course.id"]),
            sa.ForeignKeyConstraint(["question_id"], ["qb_question.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "enterprise_id",
                "user_id",
                "course_id",
                "question_id",
                name="uq_wrong_ent_user_course_question",
            ),
            mysql_charset="utf8mb4",
        )
    safe_create_index("ix_exam_wrong_question_enterprise_id", "exam_wrong_question", ["enterprise_id"], unique=False)
    safe_create_index("ix_exam_wrong_question_user_id", "exam_wrong_question", ["user_id"], unique=False)
    safe_create_index("ix_exam_wrong_question_course_id", "exam_wrong_question", ["course_id"], unique=False)
    safe_create_index("ix_exam_wrong_question_question_id", "exam_wrong_question", ["question_id"], unique=False)


def downgrade() -> None:
    if has_table("exam_wrong_question"):
        if has_index("exam_wrong_question", "ix_exam_wrong_question_question_id"):
            op.drop_index("ix_exam_wrong_question_question_id", table_name="exam_wrong_question")
        if has_index("exam_wrong_question", "ix_exam_wrong_question_course_id"):
            op.drop_index("ix_exam_wrong_question_course_id", table_name="exam_wrong_question")
        if has_index("exam_wrong_question", "ix_exam_wrong_question_user_id"):
            op.drop_index("ix_exam_wrong_question_user_id", table_name="exam_wrong_question")
        if has_index("exam_wrong_question", "ix_exam_wrong_question_enterprise_id"):
            op.drop_index("ix_exam_wrong_question_enterprise_id", table_name="exam_wrong_question")
        op.drop_table("exam_wrong_question")

