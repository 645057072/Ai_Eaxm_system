# -*- coding: utf-8 -*-
"""考试服务记录：考生交卷后自动生成（得分与是否通过）。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExamServiceRecord(Base):
    """交卷快照：便于考试服务列表展示。"""

    __tablename__ = "exam_service_record"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("exam_attempt.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        comment="对应作答记录",
    )
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("sys_enterprise.id"), index=True, comment="所属企业")
    exam_no: Mapped[str] = mapped_column(String(64), index=True, comment="考试编号（场次编码）")
    course_name: Mapped[str] = mapped_column(String(200), default="", comment="课程名称快照")
    paper_title: Mapped[str] = mapped_column(String(200), default="", comment="试卷名称快照")
    enterprise_name: Mapped[str] = mapped_column(String(200), default="", comment="企业名称快照")
    student_display: Mapped[str] = mapped_column(String(200), default="", comment="学员展示")
    score: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"), comment="得分")
    passed: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否通过（得分>=试卷及格分）")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
