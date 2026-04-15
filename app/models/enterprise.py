# -*- coding: utf-8 -*-
"""企业信息。"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.question import Question
    from app.models.user import User


class Enterprise(Base):
    """企业档案（基础信息）。"""

    __tablename__ = "sys_enterprise"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enterprise_code: Mapped[str] = mapped_column(String(64), index=True, unique=True, comment="企业编码")
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_enterprise.id"), index=True, nullable=True, comment="上级单位"
    )
    name: Mapped[str] = mapped_column(String(200), comment="企业名称")
    tax_id: Mapped[str] = mapped_column(String(32), index=True, comment="纳税人识别号")
    license_file_path: Mapped[Optional[str]] = mapped_column(String(512), comment="营业执照附件存储路径")
    address_phone: Mapped[Optional[str]] = mapped_column(String(500), comment="地址电话")
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), comment="联系人")
    industry: Mapped[Optional[str]] = mapped_column(String(500), comment="行业信息")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parent: Mapped[Optional["Enterprise"]] = relationship(
        "Enterprise", remote_side="Enterprise.id", back_populates="children"
    )
    children: Mapped[List["Enterprise"]] = relationship("Enterprise", back_populates="parent")

    users: Mapped[List["User"]] = relationship("User", back_populates="enterprise")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="enterprise")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="enterprise")
