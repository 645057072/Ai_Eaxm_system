# -*- coding: utf-8 -*-
"""试卷等级表；试卷档案扩展字段；试卷题目项自动拆分。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "paper_level",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("level_code", sa.String(length=64), nullable=False, comment="等级编号"),
        sa.Column("level_name", sa.String(length=200), nullable=False, comment="等级名称"),
        sa.Column("title_series", sa.String(length=200), nullable=False, comment="职称系列"),
        sa.Column("enterprise_id", sa.Integer(), nullable=False, comment="所属企业"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["sys_user.id"]),
        sa.ForeignKeyConstraint(["enterprise_id"], ["sys_enterprise.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enterprise_id", "level_code", name="uq_paper_level_ent_code"),
    )
    op.create_index("ix_paper_level_level_code", "paper_level", ["level_code"], unique=False)
    op.create_index("ix_paper_level_enterprise_id", "paper_level", ["enterprise_id"], unique=False)
    op.create_index("ix_paper_level_created_by", "paper_level", ["created_by"], unique=False)

    op.add_column("exam_paper", sa.Column("paper_no", sa.String(length=64), nullable=True, comment="试卷编号"))
    op.add_column("exam_paper", sa.Column("course_id", sa.Integer(), nullable=True, comment="关联课程"))
    op.add_column("exam_paper", sa.Column("paper_type", sa.String(length=32), nullable=False, server_default="formal", comment="试卷类型"))
    op.add_column("exam_paper", sa.Column("level_id", sa.Integer(), nullable=True, comment="试卷等级"))
    op.add_column("exam_paper", sa.Column("composition_rules", sa.JSON(), nullable=True, comment="组卷规则快照"))
    op.create_foreign_key("fk_exam_paper_course_id", "exam_paper", "sys_course", ["course_id"], ["id"])
    op.create_foreign_key(
        "fk_exam_paper_level_id",
        "exam_paper",
        "paper_level",
        ["level_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_exam_paper_paper_no", "exam_paper", ["paper_no"], unique=True)
    op.create_index("ix_exam_paper_course_id", "exam_paper", ["course_id"], unique=False)
    op.create_index("ix_exam_paper_paper_type", "exam_paper", ["paper_type"], unique=False)
    op.create_index("ix_exam_paper_level_id", "exam_paper", ["level_id"], unique=False)

    op.add_column(
        "exam_paper_item",
        sa.Column("auto_split_count", sa.Integer(), nullable=False, server_default="1", comment="自动拆分题目数量"),
    )


def downgrade() -> None:
    op.drop_column("exam_paper_item", "auto_split_count")
    op.drop_index("ix_exam_paper_level_id", table_name="exam_paper")
    op.drop_index("ix_exam_paper_paper_type", table_name="exam_paper")
    op.drop_index("ix_exam_paper_course_id", table_name="exam_paper")
    op.drop_constraint("fk_exam_paper_level_id", "exam_paper", type_="foreignkey")
    op.drop_constraint("fk_exam_paper_course_id", "exam_paper", type_="foreignkey")
    op.drop_index("ix_exam_paper_paper_no", table_name="exam_paper")
    op.drop_column("exam_paper", "composition_rules")
    op.drop_column("exam_paper", "level_id")
    op.drop_column("exam_paper", "paper_type")
    op.drop_column("exam_paper", "course_id")
    op.drop_column("exam_paper", "paper_no")
    op.drop_table("paper_level")
