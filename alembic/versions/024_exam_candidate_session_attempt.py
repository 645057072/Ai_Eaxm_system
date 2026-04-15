# -*- coding: utf-8 -*-
"""考生管理：关联场次与最近作答、作答时长；唯一键改为企业+考试编号+学员。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "024"
down_revision: Union[str, None] = "023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exam_candidate",
        sa.Column("session_id", sa.Integer(), nullable=True, comment="关联考试场次"),
    )
    op.add_column(
        "exam_candidate",
        sa.Column("last_attempt_id", sa.Integer(), nullable=True, comment="最近一次作答记录"),
    )
    op.add_column(
        "exam_candidate",
        sa.Column(
            "answer_duration_seconds",
            sa.Integer(),
            nullable=True,
            comment="在线作答时长（秒），交卷后写入",
        ),
    )
    op.create_foreign_key(
        "fk_exam_candidate_session_id",
        "exam_candidate",
        "exam_session",
        ["session_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_exam_candidate_last_attempt_id",
        "exam_candidate",
        "exam_attempt",
        ["last_attempt_id"],
        ["id"],
    )
    op.drop_constraint("uq_exam_candidate_ent_exam_no", "exam_candidate", type_="unique")
    op.create_unique_constraint(
        "uq_exam_candidate_ent_exam_no_student",
        "exam_candidate",
        ["enterprise_id", "exam_no", "student_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_exam_candidate_ent_exam_no_student", "exam_candidate", type_="unique")
    op.create_unique_constraint(
        "uq_exam_candidate_ent_exam_no",
        "exam_candidate",
        ["enterprise_id", "exam_no"],
    )
    op.drop_constraint("fk_exam_candidate_last_attempt_id", "exam_candidate", type_="foreignkey")
    op.drop_constraint("fk_exam_candidate_session_id", "exam_candidate", type_="foreignkey")
    op.drop_column("exam_candidate", "answer_duration_seconds")
    op.drop_column("exam_candidate", "last_attempt_id")
    op.drop_column("exam_candidate", "session_id")
