# -*- coding: utf-8 -*-
"""学员档案表：student。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.migrate_compat import has_index, has_table, safe_create_index

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not has_table("student"):
        op.create_table(
            "student",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("student_no", sa.String(length=64), nullable=False, comment="学员编号"),
            sa.Column("full_name", sa.String(length=100), nullable=False, comment="姓名"),
            sa.Column("gender", sa.String(length=10), nullable=True, comment="性别"),
            sa.Column("birth_month", sa.String(length=7), nullable=True, comment="出生年月（YYYY-MM）"),
            sa.Column("company_name", sa.String(length=200), nullable=True, comment="所属公司"),
            sa.Column("phone", sa.String(length=50), nullable=True, comment="联系电话"),
            sa.Column("id_card_no", sa.String(length=32), nullable=True, comment="身份证号"),
            sa.Column("address_phone", sa.String(length=500), nullable=True, comment="地址电话"),
            sa.Column("remark", sa.Text(), nullable=True, comment="备注"),
            sa.Column("enterprise_id", sa.Integer(), nullable=True, comment="所属企业（为空则按创建者企业归属）"),
            sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人"),
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
            sa.ForeignKeyConstraint(["created_by"], ["sys_user.id"]),
            sa.PrimaryKeyConstraint("id"),
            mysql_charset="utf8mb4",
        )
    safe_create_index("ix_student_student_no", "student", ["student_no"], unique=False)
    safe_create_index("ix_student_full_name", "student", ["full_name"], unique=False)
    safe_create_index("ix_student_company_name", "student", ["company_name"], unique=False)
    safe_create_index("ix_student_enterprise_id", "student", ["enterprise_id"], unique=False)
    safe_create_index("ix_student_created_by", "student", ["created_by"], unique=False)


def downgrade() -> None:
    if has_table("student"):
        if has_index("student", "ix_student_created_by"):
            op.drop_index("ix_student_created_by", table_name="student")
        if has_index("student", "ix_student_enterprise_id"):
            op.drop_index("ix_student_enterprise_id", table_name="student")
        if has_index("student", "ix_student_company_name"):
            op.drop_index("ix_student_company_name", table_name="student")
        if has_index("student", "ix_student_full_name"):
            op.drop_index("ix_student_full_name", table_name="student")
        if has_index("student", "ix_student_student_no"):
            op.drop_index("ix_student_student_no", table_name="student")
        op.drop_table("student")

