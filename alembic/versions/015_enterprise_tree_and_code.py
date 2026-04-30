# -*- coding: utf-8 -*-
"""企业：企业编码、上级单位（树形）。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

from app.db.migrate_compat import has_fk, has_index, safe_create_fk, safe_create_index

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = insp.get_columns(table)
    return any((c.get("name") == col) for c in cols)


def upgrade() -> None:
    if not _has_column("sys_enterprise", "enterprise_code"):
        op.add_column(
            "sys_enterprise",
            sa.Column("enterprise_code", sa.String(length=64), nullable=True, comment="企业编码"),
        )
    if not _has_column("sys_enterprise", "parent_id"):
        op.add_column(
            "sys_enterprise",
            sa.Column("parent_id", sa.Integer(), nullable=True, comment="上级单位"),
        )

    bind = op.get_bind()
    bind.execute(
        text(
            "UPDATE sys_enterprise SET enterprise_code = CONCAT('E', LPAD(id, 6, '0')) "
            "WHERE enterprise_code IS NULL OR enterprise_code = ''"
        )
    )

    op.alter_column(
        "sys_enterprise",
        "enterprise_code",
        existing_type=sa.String(length=64),
        nullable=False,
        existing_comment="企业编码",
    )

    safe_create_index("ix_sys_enterprise_enterprise_code", "sys_enterprise", ["enterprise_code"], unique=True)
    safe_create_index("ix_sys_enterprise_parent_id", "sys_enterprise", ["parent_id"], unique=False)
    safe_create_fk(
        "fk_sys_enterprise_parent",
        "sys_enterprise",
        "sys_enterprise",
        ["parent_id"],
        ["id"],
    )


def downgrade() -> None:
    if has_fk("sys_enterprise", "fk_sys_enterprise_parent"):
        op.drop_constraint("fk_sys_enterprise_parent", "sys_enterprise", type_="foreignkey")
    if has_index("sys_enterprise", "ix_sys_enterprise_parent_id"):
        op.drop_index("ix_sys_enterprise_parent_id", table_name="sys_enterprise")
    if has_index("sys_enterprise", "ix_sys_enterprise_enterprise_code"):
        op.drop_index("ix_sys_enterprise_enterprise_code", table_name="sys_enterprise")
    op.drop_column("sys_enterprise", "parent_id")
    op.drop_column("sys_enterprise", "enterprise_code")
