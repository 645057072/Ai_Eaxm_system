# -*- coding: utf-8 -*-
"""学员档案：移除所属公司字段。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        op.drop_index("ix_student_company_name", table_name="student")
    except Exception:
        # 不同数据库可能不存在该索引
        pass
    op.drop_column("student", "company_name")


def downgrade() -> None:
    op.add_column("student", sa.Column("company_name", sa.String(length=200), nullable=True, comment="所属公司"))
    op.create_index("ix_student_company_name", "student", ["company_name"], unique=False)

