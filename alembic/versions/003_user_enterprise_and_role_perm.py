# -*- coding: utf-8 -*-
"""用户所属企业、角色功能授权表。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    # 保证存在至少一条企业记录
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
    op.add_column("sys_user", sa.Column("enterprise_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_sys_user_enterprise", "sys_user", "sys_enterprise", ["enterprise_id"], ["id"])
    op.create_index("ix_sys_user_enterprise_id", "sys_user", ["enterprise_id"], unique=False)
    bind.execute(sa.text("UPDATE sys_user SET enterprise_id = :eid WHERE enterprise_id IS NULL"), {"eid": eid})
    op.alter_column("sys_user", "enterprise_id", existing_type=sa.Integer(), nullable=False)

    op.create_table(
        "sys_role_permission",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_code", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["sys_role.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_code"),
        mysql_charset="utf8mb4",
    )


def downgrade() -> None:
    op.drop_table("sys_role_permission")
    op.drop_constraint("fk_sys_user_enterprise", "sys_user", type_="foreignkey")
    op.drop_index("ix_sys_user_enterprise_id", table_name="sys_user")
    op.drop_column("sys_user", "enterprise_id")
