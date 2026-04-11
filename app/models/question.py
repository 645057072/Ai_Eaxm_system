# -*- coding: utf-8 -*-
"""题库题目。"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.exam import ExamPaperItem


class Question(Base):
    """题目：判断、单选、多选、填空。"""

    __tablename__ = "qb_question"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # judge / single / multiple / fill
    q_type: Mapped[str] = mapped_column(String(16), index=True, comment="题型")
    stem: Mapped[str] = mapped_column(Text, comment="题干")
    options_json: Mapped[Optional[Any]] = mapped_column(JSON, comment="选项列表 JSON")
    answer_json: Mapped[Any] = mapped_column(JSON, comment="标准答案 JSON")
    analysis: Mapped[Optional[str]] = mapped_column(Text, comment="解析")
    difficulty: Mapped[int] = mapped_column(Integer, default=1, comment="难度 1-5")
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True, comment="draft/published")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    creator: Mapped[Optional["User"]] = relationship(
        back_populates="questions_created", foreign_keys=[created_by]
    )
    paper_items: Mapped[List["ExamPaperItem"]] = relationship(back_populates="question")
