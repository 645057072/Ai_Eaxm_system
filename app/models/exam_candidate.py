# -*- coding: utf-8 -*-
"""考生档案（考试管理）。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExamCandidate(Base):
    """考生：考试编号、企业、课程、学员。"""

    __tablename__ = "exam_candidate"
    __table_args__ = (
        UniqueConstraint("enterprise_id", "exam_no", name="uq_exam_candidate_ent_exam_no"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exam_no: Mapped[str] = mapped_column(String(64), index=True, comment="考试编号")
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("sys_enterprise.id"), index=True, comment="所属企业")
    course_id: Mapped[int] = mapped_column(ForeignKey("sys_course.id"), index=True, comment="课程")
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), index=True, comment="学员")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    enterprise = relationship("Enterprise", lazy="joined")
    course = relationship("Course", lazy="joined")
    student = relationship("Student", lazy="joined")
