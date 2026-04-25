# -*- coding: utf-8 -*-
"""用户所属企业、角色功能授权表。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        return insp.has_table(table)
    except Exception:
        return table in (insp.get_table_names() or [])


def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        cols = insp.get_columns(table) or []
        return any((c.get("name") == col) for c in cols)
    except Exception:
        return False


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        idx = insp.get_indexes(table) or []
        return any((i.get("name") == index_name) for i in idx)
    except Exception:
        return False


def _has_fk(table: str, fk_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        fks = insp.get_foreign_keys(table) or []
        return any((fk.get("name") == fk_name) for fk in fks)
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    # 保证存在至少一条企业记录
    if _has_table("sys_enterprise"):
        r = bind.execute(sa.text("SELECT COUNT(*) FROM sys_enterprise")).scalar()
        if r == 0:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO sys_enterprise
                    (name, tax_id, license_file_path, address_phone, contact_person, industry)
                    VALUES ('默认企业', 'DEFAULT000000000000000', NULL, NULL, NULL, NULL)
                    """
                )
            )
        eid = bind.execute(sa.text("SELECT id FROM sys_enterprise ORDER BY id ASC LIMIT 1")).scalar()
    else:
        # 理论上不会发生（002 会建表），但为幂等防御
        eid = None

    # 幂等：历史库可能已存在 enterprise_id / 索引 / 外键
    if not _has_column("sys_user", "enterprise_id"):
        op.add_column("sys_user", sa.Column("enterprise_id", sa.Integer(), nullable=True))
    if not _has_fk("sys_user", "fk_sys_user_enterprise"):
        try:
            op.create_foreign_key("fk_sys_user_enterprise", "sys_user", "sys_enterprise", ["enterprise_id"], ["id"])
        except Exception:
            pass
    if not _has_index("sys_user", "ix_sys_user_enterprise_id"):
        try:
            op.create_index("ix_sys_user_enterprise_id", "sys_user", ["enterprise_id"], unique=False)
        except Exception:
            pass
    if eid is not None:
        bind.execute(sa.text("UPDATE sys_user SET enterprise_id = :eid WHERE enterprise_id IS NULL"), {"eid": eid})
        try:
            op.alter_column("sys_user", "enterprise_id", existing_type=sa.Integer(), nullable=False)
        except Exception:
            # 兼容：某些环境 enterprise_id 可能已是 NOT NULL
            pass

    if not _has_table("sys_role_permission"):
        op.create_table(
            "sys_role_permission",
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.Column("permission_code", sa.String(length=128), nullable=False),
            sa.ForeignKeyConstraint(["role_id"], ["sys_role.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("role_id", "permission_code"),
            mysql_charset="utf8mb4",
        )


def downgrade() -> None:
    if _has_table("sys_role_permission"):
        op.drop_table("sys_role_permission")
    try:
        op.drop_constraint("fk_sys_user_enterprise", "sys_user", type_="foreignkey")
    except Exception:
        pass
    if _has_index("sys_user", "ix_sys_user_enterprise_id"):
        op.drop_index("ix_sys_user_enterprise_id", table_name="sys_user")
    if _has_column("sys_user", "enterprise_id"):
        op.drop_column("sys_user", "enterprise_id")
