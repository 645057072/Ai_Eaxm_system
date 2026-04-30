# -*- coding: utf-8 -*-
"""学员档案：移除所属公司字段。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.migrate_compat import has_column, has_index, safe_create_index

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if has_index("student", "ix_student_company_name"):
        try:
            op.drop_index("ix_student_company_name", table_name="student")
        except Exception:
            pass
    if has_column("student", "company_name"):
        op.drop_column("student", "company_name")


def downgrade() -> None:
    if not has_column("student", "company_name"):
        op.add_column("student", sa.Column("company_name", sa.String(length=200), nullable=True, comment="所属公司"))
    safe_create_index("ix_student_company_name", "student", ["company_name"], unique=False)

