# -*- coding: utf-8 -*-
"""企业信息表 sys_enterprise。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        return insp.has_table(table)
    except Exception:
        # 兼容：部分方言/权限问题下 has_table 可能抛异常
        return table in (insp.get_table_names() or [])


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        idx = insp.get_indexes(table) or []
        return any((i.get("name") == index_name) for i in idx)
    except Exception:
        return False


def upgrade() -> None:
    # 幂等：历史上可能因迁移中断/手工建表导致 sys_enterprise 已存在
    if not _has_table("sys_enterprise"):
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
    if not _has_index("sys_enterprise", "ix_sys_enterprise_tax_id"):
        op.create_index("ix_sys_enterprise_tax_id", "sys_enterprise", ["tax_id"], unique=False)


def downgrade() -> None:
    if _has_table("sys_enterprise"):
        if _has_index("sys_enterprise", "ix_sys_enterprise_tax_id"):
            op.drop_index("ix_sys_enterprise_tax_id", table_name="sys_enterprise")
        op.drop_table("sys_enterprise")
