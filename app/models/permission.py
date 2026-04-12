# -*- coding: utf-8 -*-
"""角色与功能点授权。"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RolePermission(Base):
    """角色拥有的功能点编码（与 permission_catalog 中 code 对应）。"""

    __tablename__ = "sys_role_permission"

    role_id: Mapped[int] = mapped_column(ForeignKey("sys_role.id", ondelete="CASCADE"), primary_key=True)
    permission_code: Mapped[str] = mapped_column(String(128), primary_key=True)
