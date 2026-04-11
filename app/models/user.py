# -*- coding: utf-8 -*-
"""用户与角色。"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.exam import ExamPaper, ExamSession, ExamAttempt
    from app.models.question import Question


class Role(Base):
    """角色：管理员、教师、考生。"""

    __tablename__ = "sys_role"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), comment="角色名称")
    code: Mapped[str] = mapped_column(String(32), unique=True, comment="角色编码")
    description: Mapped[Optional[str]] = mapped_column(String(255), comment="说明")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[List["User"]] = relationship(back_populates="role")


class User(Base):
    """系统用户。"""

    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(64))
    role_id: Mapped[int] = mapped_column(ForeignKey("sys_role.id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    role: Mapped["Role"] = relationship(back_populates="users", lazy="joined")
    questions_created: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="creator",
        foreign_keys="Question.created_by",
    )
    papers_created: Mapped[List["ExamPaper"]] = relationship(
        "ExamPaper",
        back_populates="creator",
        foreign_keys="ExamPaper.created_by",
    )
    sessions_created: Mapped[List["ExamSession"]] = relationship(
        "ExamSession",
        back_populates="creator",
        foreign_keys="ExamSession.created_by",
    )
    attempts: Mapped[List["ExamAttempt"]] = relationship(back_populates="user")
