# -*- coding: utf-8 -*-
"""试卷等级：与职称系列、企业绑定。"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.enterprise import Enterprise
    from app.models.user import User


class PaperLevel(Base):
    """试卷等级（基础信息）。"""

    __tablename__ = "paper_level"
    __table_args__ = (UniqueConstraint("enterprise_id", "level_code", name="uq_paper_level_ent_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level_code: Mapped[str] = mapped_column(String(64), index=True, comment="等级编号")
    level_name: Mapped[str] = mapped_column(String(200), comment="等级名称")
    title_series: Mapped[str] = mapped_column(String(200), comment="职称系列")
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("sys_enterprise.id"), index=True, comment="所属企业")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    enterprise: Mapped["Enterprise"] = relationship("Enterprise", lazy="joined")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by], lazy="joined")
