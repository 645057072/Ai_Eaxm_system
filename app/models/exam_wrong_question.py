# -*- coding: utf-8 -*-
"""错题集：交卷后将错题/未答题纳入，答对后移除。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExamWrongQuestion(Base):
    """错题集条目（按用户维度）。"""

    __tablename__ = "exam_wrong_question"
    __table_args__ = (
        UniqueConstraint(
            "enterprise_id",
            "user_id",
            "course_id",
            "question_id",
            name="uq_wrong_ent_user_course_question",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(
        ForeignKey("sys_enterprise.id"), index=True, comment="所属企业"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("sys_user.id", ondelete="CASCADE"), index=True, comment="用户"
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("sys_course.id"), index=True, comment="课程"
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("qb_question.id", ondelete="CASCADE"), index=True, comment="题目"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

