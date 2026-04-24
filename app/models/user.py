# -*- coding: utf-8 -*-
"""用户与角色。"""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.student import Student

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.enterprise import Enterprise
    from app.models.exam import ExamPaper, ExamSession, ExamAttempt
    from app.models.question import Question
    from app.models.student import Student


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
    # 系统全局管理员（admin）可不绑定企业；其余用户须有所属企业
    enterprise_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_enterprise.id"), nullable=True, index=True, comment="所属企业"
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("sys_role.id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    student_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("student.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
        comment="关联学员ID",
    )
    # 不在 DDL 中使用 CURRENT_DATE/CURDATE 默认值：MySQL 5.7 等对 DATE 列不支持表达式默认值，create_all 会失败
    enable_date: Mapped[date] = mapped_column(Date, default=date.today, comment="启用日期")
    expire_date: Mapped[Optional[date]] = mapped_column(Date, comment="失效日期")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    role: Mapped["Role"] = relationship(back_populates="users", lazy="joined")
    enterprise: Mapped[Optional["Enterprise"]] = relationship("Enterprise", back_populates="users")
    # 显式指定关联条件，避免部分环境下外键识别失败导致 Mapper 初始化报错
    student: Mapped[Optional["Student"]] = relationship(
        Student,
        lazy="joined",
        primaryjoin=lambda: User.student_id == Student.id,
        foreign_keys=lambda: [User.student_id],
    )
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
    sessions_published: Mapped[List["ExamSession"]] = relationship(
        "ExamSession",
        back_populates="publisher",
        foreign_keys="ExamSession.published_by",
    )
    attempts: Mapped[List["ExamAttempt"]] = relationship(back_populates="user")
    courses_created: Mapped[List["Course"]] = relationship("Course", back_populates="creator")
