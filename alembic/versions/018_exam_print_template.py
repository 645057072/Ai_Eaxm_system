# -*- coding: utf-8 -*-
"""试卷打印模板表。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exam_print_template",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("template_no", sa.String(length=64), nullable=False),
        sa.Column("template_name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("module_code", sa.String(length=64), nullable=False),
        sa.Column("menu_code", sa.String(length=128), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("paper_format", sa.String(length=32), nullable=False, server_default="A4"),
        sa.Column("layout_json", sa.JSON(), nullable=False),
        sa.Column("publish_scope_enterprise_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["sys_course.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_user.id"]),
        sa.ForeignKeyConstraint(["publish_scope_enterprise_id"], ["sys_enterprise.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exam_print_template_template_no", "exam_print_template", ["template_no"], unique=True)
    op.create_index("ix_exam_print_template_module_code", "exam_print_template", ["module_code"])
    op.create_index("ix_exam_print_template_menu_code", "exam_print_template", ["menu_code"])
    op.create_index("ix_exam_print_template_course_id", "exam_print_template", ["course_id"])
    op.create_index("ix_exam_print_template_paper_format", "exam_print_template", ["paper_format"])
    op.create_index(
        "ix_exam_print_template_publish_scope_enterprise_id",
        "exam_print_template",
        ["publish_scope_enterprise_id"],
    )
    op.create_index("ix_exam_print_template_status", "exam_print_template", ["status"])


def downgrade() -> None:
    op.drop_index("ix_exam_print_template_status", table_name="exam_print_template")
    op.drop_index("ix_exam_print_template_publish_scope_enterprise_id", table_name="exam_print_template")
    op.drop_index("ix_exam_print_template_paper_format", table_name="exam_print_template")
    op.drop_index("ix_exam_print_template_course_id", table_name="exam_print_template")
    op.drop_index("ix_exam_print_template_menu_code", table_name="exam_print_template")
    op.drop_index("ix_exam_print_template_module_code", table_name="exam_print_template")
    op.drop_index("ix_exam_print_template_template_no", table_name="exam_print_template")
    op.drop_table("exam_print_template")
