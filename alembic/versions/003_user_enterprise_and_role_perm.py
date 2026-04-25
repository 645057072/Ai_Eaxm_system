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


def _get_columns(table: str) -> list[dict]:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        return list(insp.get_columns(table) or [])
    except Exception:
        return []


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
            # 兼容：不同环境下 sys_enterprise 字段可能不一致（如 enterprise_code 为 NOT NULL 且无默认值）
            cols = _get_columns("sys_enterprise")
            col_names = {c.get("name") for c in cols if c.get("name")}
            default_tax_id = "DEFAULT000000000000000"

            insert_cols: list[str] = []
            insert_vals: dict[str, object] = {}

            def _set(col: str, val: object) -> None:
                if col in col_names:
                    insert_cols.append(col)
                    insert_vals[col] = val

            _set("name", "默认企业")
            _set("tax_id", default_tax_id)
            _set("license_file_path", None)
            _set("address_phone", None)
            _set("contact_person", None)
            _set("industry", None)
            # 常见变体字段：企业编码（可能为 NOT NULL 且无默认值）
            if "enterprise_code" in col_names and "enterprise_code" not in insert_vals:
                _set("enterprise_code", "DEFAULT")

            if insert_cols:
                col_sql = ", ".join(insert_cols)
                val_sql = ", ".join([f":{c}" for c in insert_cols])
                bind.execute(
                    sa.text(f"INSERT INTO sys_enterprise ({col_sql}) VALUES ({val_sql})"),
                    insert_vals,
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
