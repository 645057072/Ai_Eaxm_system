# -*- coding: utf-8 -*-
"""试卷、场次、作答。"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.question import Question


class ExamPaper(Base):
    """试卷（组卷容器）。"""

    __tablename__ = "exam_paper"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, comment="考试时长分钟")
    total_score: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("100.00"))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    creator: Mapped[Optional["User"]] = relationship(
        back_populates="papers_created", foreign_keys=[created_by]
    )
    items: Mapped[List["ExamPaperItem"]] = relationship(
        back_populates="paper", order_by="ExamPaperItem.sort_order", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["ExamSession"]] = relationship(back_populates="paper")


class ExamPaperItem(Base):
    """试卷内题目及分值。"""

    __tablename__ = "exam_paper_item"
    __table_args__ = (UniqueConstraint("paper_id", "question_id", name="uq_paper_question"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("exam_paper.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("qb_question.id", ondelete="CASCADE"), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1.00"))

    paper: Mapped["ExamPaper"] = relationship(back_populates="items")
    question: Mapped["Question"] = relationship(back_populates="paper_items")


class ExamSession(Base):
    """考试场次：绑定试卷与开放时间。"""

    __tablename__ = "exam_session"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("exam_paper.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # draft / published / closed
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    paper: Mapped["ExamPaper"] = relationship(back_populates="sessions")
    creator: Mapped[Optional["User"]] = relationship(
        back_populates="sessions_created", foreign_keys=[created_by]
    )
    attempts: Mapped[List["ExamAttempt"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ExamAttempt(Base):
    """考生某次考试作答实例。"""

    __tablename__ = "exam_attempt"
    __table_args__ = (UniqueConstraint("session_id", "user_id", name="uq_session_user_attempt"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_session.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # in_progress / submitted / timeout
    status: Mapped[str] = mapped_column(String(16), default="in_progress", index=True)
    total_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    session: Mapped["ExamSession"] = relationship(back_populates="attempts")
    user: Mapped["User"] = relationship(back_populates="attempts")
    answers: Mapped[List["ExamAnswer"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")


class ExamAnswer(Base):
    """单题作答记录。"""

    __tablename__ = "exam_answer"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("exam_attempt.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("qb_question.id", ondelete="CASCADE"), index=True)
    user_answer_json: Mapped[Optional[Any]] = mapped_column(JSON, comment="考生答案")
    score_awarded: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    attempt: Mapped["ExamAttempt"] = relationship(back_populates="answers")
