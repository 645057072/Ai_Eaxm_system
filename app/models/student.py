# -*- coding: utf-8 -*-
"""学员档案。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Student(Base):
    """学员档案（系统管理-基础信息）。"""

    __tablename__ = "student"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_no: Mapped[str] = mapped_column(String(64), index=True, comment="学员编号")
    full_name: Mapped[str] = mapped_column(String(100), index=True, comment="姓名")
    gender: Mapped[Optional[str]] = mapped_column(String(10), comment="性别")
    birth_month: Mapped[Optional[str]] = mapped_column(String(7), comment="出生年月（YYYY-MM）")
    company_name: Mapped[Optional[str]] = mapped_column(String(200), index=True, comment="所属公司")
    phone: Mapped[Optional[str]] = mapped_column(String(50), comment="联系电话")
    id_card_no: Mapped[Optional[str]] = mapped_column(String(32), comment="身份证号")
    address_phone: Mapped[Optional[str]] = mapped_column(String(500), comment="地址电话")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")
    enterprise_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_enterprise.id"), index=True, comment="所属企业")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), index=True, comment="创建人")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    enterprise = relationship("Enterprise", lazy="joined")
    creator = relationship("User", lazy="joined", foreign_keys=[created_by])

