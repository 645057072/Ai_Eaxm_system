# -*- coding: utf-8 -*-
"""企业信息表 sys_enterprise。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sys_enterprise",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False, comment="企业名称"),
        sa.Column("tax_id", sa.String(length=32), nullable=False, comment="纳税人识别号"),
        sa.Column("license_file_path", sa.String(length=512), nullable=True, comment="营业执照附件存储路径"),
        sa.Column("address_phone", sa.String(length=500), nullable=True, comment="地址电话"),
        sa.Column("contact_person", sa.String(length=100), nullable=True, comment="联系人"),
        sa.Column("industry", sa.String(length=500), nullable=True, comment="行业信息"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_sys_enterprise_tax_id", "sys_enterprise", ["tax_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sys_enterprise_tax_id", table_name="sys_enterprise")
    op.drop_table("sys_enterprise")
