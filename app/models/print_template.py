# -*- coding: utf-8 -*-
"""试卷打印模板（按课程关联，供后期组卷打印调用）。"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.enterprise import Enterprise
    from app.models.user import User


class PrintTemplate(Base):
    """打印模板：模块/菜单/课程/纸张格式与版式 JSON。"""

    __tablename__ = "exam_print_template"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="模板编号")
    template_name: Mapped[str] = mapped_column(String(200), default="", comment="模板名称")
    module_code: Mapped[str] = mapped_column(String(64), index=True, comment="业务模块编码")
    menu_code: Mapped[str] = mapped_column(String(128), index=True, comment="关联菜单功能点编码")
    course_id: Mapped[int] = mapped_column(ForeignKey("sys_course.id", ondelete="CASCADE"), index=True)
    paper_format: Mapped[str] = mapped_column(String(32), default="A4", index=True, comment="纸张规格 A4/A3/B5/CUSTOM")
    layout_json: Mapped[dict[str, Any]] = mapped_column(JSON, comment="版式与样式 JSON")
    publish_scope_enterprise_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_enterprise.id"),
        nullable=True,
        index=True,
        comment="发布后限定企业；空表示全局可用",
    )
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True, comment="draft|published")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    course: Mapped["Course"] = relationship("Course", back_populates="print_templates")
    publish_scope_enterprise: Mapped[Optional["Enterprise"]] = relationship(
        "Enterprise", foreign_keys=[publish_scope_enterprise_id]
    )
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
