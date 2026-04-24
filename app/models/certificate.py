# -*- coding: utf-8 -*-
"""证书模板与颁发记录。"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.enterprise import Enterprise
    from app.models.exam_service_record import ExamServiceRecord
    from app.models.user import User


class CertTemplate(Base):
    """证书模板：版式 JSON + 可选关联课程。"""

    __tablename__ = "exam_cert_template"
    __table_args__ = (UniqueConstraint("enterprise_id", "cert_code", name="uq_cert_template_ent_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("sys_enterprise.id"), index=True, comment="所属企业")
    cert_code: Mapped[str] = mapped_column(String(64), index=True, comment="模板编码（企业内唯一）")
    name: Mapped[str] = mapped_column(String(200), default="", comment="模板名称")
    course_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_course.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联课程；空为通用"
    )
    layout_json: Mapped[dict[str, Any]] = mapped_column(JSON, comment="版式与文案占位符 JSON")
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True, comment="draft|published")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    enterprise: Mapped["Enterprise"] = relationship("Enterprise", foreign_keys=[enterprise_id])
    course: Mapped[Optional["Course"]] = relationship("Course", foreign_keys=[course_id])
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    records: Mapped[List["CertRecord"]] = relationship("CertRecord", back_populates="template")


class CertRecord(Base):
    """已颁发证书（关联考试服务记录与模板）。"""

    __tablename__ = "exam_cert_record"
    __table_args__ = (
        UniqueConstraint("certificate_no", name="uq_cert_record_no"),
        UniqueConstraint("exam_service_record_id", "cert_template_id", name="uq_cert_record_svc_tpl"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("sys_enterprise.id"), index=True)
    cert_template_id: Mapped[int] = mapped_column(ForeignKey("exam_cert_template.id", ondelete="RESTRICT"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True, comment="获证人")
    exam_service_record_id: Mapped[int] = mapped_column(
        ForeignKey("exam_service_record.id", ondelete="CASCADE"), index=True
    )
    certificate_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="证书编号")
    student_display: Mapped[str] = mapped_column(String(200), default="")
    course_name: Mapped[str] = mapped_column(String(200), default="")
    paper_title: Mapped[str] = mapped_column(String(200), default="")
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    issued_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), nullable=True, comment="颁发人")

    template: Mapped["CertTemplate"] = relationship("CertTemplate", back_populates="records")
    enterprise: Mapped["Enterprise"] = relationship("Enterprise", foreign_keys=[enterprise_id])
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    issuer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[issued_by])
    service_record: Mapped["ExamServiceRecord"] = relationship("ExamServiceRecord", foreign_keys=[exam_service_record_id])
