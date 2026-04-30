# -*- coding: utf-8 -*-
"""考生表 exam_candidate：考试编号、企业、课程、学员。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.migrate_compat import has_index, has_table, safe_create_index

revision: str = "020"
down_revision: Union[str, None] = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not has_table("exam_candidate"):
        op.create_table(
            "exam_candidate",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("exam_no", sa.String(length=64), nullable=False, comment="考试编号"),
            sa.Column("enterprise_id", sa.Integer(), nullable=False, comment="所属企业"),
            sa.Column("course_id", sa.Integer(), nullable=False, comment="课程"),
            sa.Column("student_id", sa.Integer(), nullable=False, comment="学员"),
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
            sa.ForeignKeyConstraint(["course_id"], ["sys_course.id"]),
            sa.ForeignKeyConstraint(["enterprise_id"], ["sys_enterprise.id"]),
            sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("enterprise_id", "exam_no", name="uq_exam_candidate_ent_exam_no"),
            mysql_charset="utf8mb4",
        )
    safe_create_index("ix_exam_candidate_exam_no", "exam_candidate", ["exam_no"], unique=False)
    safe_create_index("ix_exam_candidate_enterprise_id", "exam_candidate", ["enterprise_id"], unique=False)
    safe_create_index("ix_exam_candidate_course_id", "exam_candidate", ["course_id"], unique=False)
    safe_create_index("ix_exam_candidate_student_id", "exam_candidate", ["student_id"], unique=False)


def downgrade() -> None:
    if has_table("exam_candidate"):
        if has_index("exam_candidate", "ix_exam_candidate_student_id"):
            op.drop_index("ix_exam_candidate_student_id", table_name="exam_candidate")
        if has_index("exam_candidate", "ix_exam_candidate_course_id"):
            op.drop_index("ix_exam_candidate_course_id", table_name="exam_candidate")
        if has_index("exam_candidate", "ix_exam_candidate_enterprise_id"):
            op.drop_index("ix_exam_candidate_enterprise_id", table_name="exam_candidate")
        if has_index("exam_candidate", "ix_exam_candidate_exam_no"):
            op.drop_index("ix_exam_candidate_exam_no", table_name="exam_candidate")
        op.drop_table("exam_candidate")
