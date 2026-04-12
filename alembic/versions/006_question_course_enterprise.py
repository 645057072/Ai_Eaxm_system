# -*- coding: utf-8 -*-
"""题目关联课程、所属企业（题库导入）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("qb_question", sa.Column("course_id", sa.Integer(), nullable=True))
    op.add_column("qb_question", sa.Column("enterprise_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_qb_question_course", "qb_question", "sys_course", ["course_id"], ["id"])
    op.create_foreign_key("fk_qb_question_enterprise", "qb_question", "sys_enterprise", ["enterprise_id"], ["id"])
    op.create_index("ix_qb_question_course_id", "qb_question", ["course_id"], unique=False)
    op.create_index("ix_qb_question_enterprise_id", "qb_question", ["enterprise_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_qb_question_enterprise_id", table_name="qb_question")
    op.drop_index("ix_qb_question_course_id", table_name="qb_question")
    op.drop_constraint("fk_qb_question_enterprise", "qb_question", type_="foreignkey")
    op.drop_constraint("fk_qb_question_course", "qb_question", type_="foreignkey")
    op.drop_column("qb_question", "enterprise_id")
    op.drop_column("qb_question", "course_id")
