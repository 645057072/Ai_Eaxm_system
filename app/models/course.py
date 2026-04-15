# -*- coding: utf-8 -*-
"""课程信息。"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.enterprise import Enterprise
    from app.models.print_template import PrintTemplate
    from app.models.question import Question
    from app.models.user import User


class Course(Base):
    """课程档案。"""

    __tablename__ = "sys_course"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), comment="课程名称")
    instructor: Mapped[str] = mapped_column(String(100), comment="讲师")
    period_text: Mapped[str] = mapped_column(String(255), comment="课程期间")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="课程简介")
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("sys_enterprise.id"), index=True, comment="所属企业")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), nullable=True, comment="创建人")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    enterprise: Mapped["Enterprise"] = relationship("Enterprise", back_populates="courses")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="course")
    creator: Mapped[Optional["User"]] = relationship("User", back_populates="courses_created")
    print_templates: Mapped[List["PrintTemplate"]] = relationship(
        "PrintTemplate",
        back_populates="course",
        foreign_keys="PrintTemplate.course_id",
    )

