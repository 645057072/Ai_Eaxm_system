# -*- coding: utf-8 -*-
"""试卷、场次、作答。"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.enterprise import Enterprise
    from app.models.paper_level import PaperLevel
    from app.models.user import User
    from app.models.question import Question


class ExamPaper(Base):
    """试卷（组卷容器）。"""

    __tablename__ = "exam_paper"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    paper_no: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, comment="试卷编号")
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_course.id"), index=True, comment="关联课程")
    paper_type: Mapped[str] = mapped_column(String(32), default="formal", index=True, comment="试卷类型")
    level_id: Mapped[Optional[int]] = mapped_column(ForeignKey("paper_level.id"), index=True, comment="试卷等级")
    composition_rules: Mapped[Optional[Any]] = mapped_column(JSON, comment="组卷规则快照")
    description: Mapped[Optional[str]] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, comment="考试时长分钟")
    total_score: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("100.00"))
    pass_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("60.00"), comment="及格率(%)，合格分=总分×及格率/100"
    )
    pass_score: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), comment="及格分(合格分)，由总分与及格率自动计算"
    )
    audit_status: Mapped[str] = mapped_column(
        String(16), default="draft", index=True, comment="审核状态：draft 草稿，reviewed 已审核"
    )
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="创建/签发日期")
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="有效期至")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    creator: Mapped[Optional["User"]] = relationship(
        back_populates="papers_created", foreign_keys=[created_by]
    )
    course: Mapped[Optional["Course"]] = relationship("Course", foreign_keys=[course_id])
    paper_level: Mapped[Optional["PaperLevel"]] = relationship("PaperLevel", foreign_keys=[level_id])
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
    auto_split_count: Mapped[int] = mapped_column(Integer, default=1, comment="自动拆分题目数量")

    paper: Mapped["ExamPaper"] = relationship(back_populates="items")
    question: Mapped["Question"] = relationship(back_populates="paper_items")


class ExamSession(Base):
    """考试场次：绑定试卷与开放时间。"""

    __tablename__ = "exam_session"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="场次编码")
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("sys_enterprise.id"), index=True, comment="所属企业")
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_course.id"), index=True, nullable=True, comment="关联课程")
    paper_id: Mapped[int] = mapped_column(ForeignKey("exam_paper.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # draft / published / closed
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), index=True)
    published_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id"), index=True, nullable=True, comment="发布人"
    )
    attempt_limit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="答题次数上限；空为不限制（练习卷）"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    paper: Mapped["ExamPaper"] = relationship(back_populates="sessions")
    enterprise: Mapped["Enterprise"] = relationship("Enterprise", foreign_keys=[enterprise_id])
    course: Mapped[Optional["Course"]] = relationship("Course", foreign_keys=[course_id])
    creator: Mapped[Optional["User"]] = relationship(
        back_populates="sessions_created", foreign_keys=[created_by]
    )
    publisher: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="sessions_published",
        foreign_keys=[published_by],
    )
    attempts: Mapped[List["ExamAttempt"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ExamAttempt(Base):
    """考生某次考试作答实例。"""

    __tablename__ = "exam_attempt"
    __table_args__ = ()

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_session.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    exam_timer_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="本次作答考试时长起算时刻（与 started_at 可区分，用于续考倒计时）",
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # in_progress / submitted / timeout
    status: Mapped[str] = mapped_column(String(16), default="in_progress", index=True)
    staged: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="练习卷暂存标记：再次进入时提示是否继续作答"
    )
    practice_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="练习卷交卷报告")
    total_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    client_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="客户端 IP（进入考试时记录，用于数智大屏地域分布）"
    )

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
