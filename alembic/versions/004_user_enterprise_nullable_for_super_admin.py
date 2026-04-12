# -*- coding: utf-8 -*-
"""系统全局管理员（admin）可不绑定所属企业：enterprise_id 允许为空。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 须先将列改为可空，再写入 NULL；否则在 NOT NULL 约束下 UPDATE 会报 1048
    op.alter_column(
        "sys_user",
        "enterprise_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE sys_user u
            INNER JOIN sys_role r ON u.role_id = r.id
            SET u.enterprise_id = NULL
            WHERE r.code = 'admin'
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    eid = bind.execute(sa.text("SELECT id FROM sys_enterprise ORDER BY id ASC LIMIT 1")).scalar()
    if eid is not None:
        bind.execute(
            sa.text("UPDATE sys_user SET enterprise_id = :eid WHERE enterprise_id IS NULL"),
            {"eid": eid},
        )
    op.alter_column(
        "sys_user",
        "enterprise_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
