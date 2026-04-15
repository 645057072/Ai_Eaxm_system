# -*- coding: utf-8 -*-
"""考试场次。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.paper import PaperOut


class ExamSessionCreate(BaseModel):
    session_code: Optional[str] = Field(None, max_length=64, description="场次编码，留空则后台自动生成")
    enterprise_id: int = Field(..., ge=1, description="所属企业（关联企业信息）")
    course_id: int = Field(..., ge=1, description="关联课程（课程管理）")
    paper_id: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None

    @field_validator("session_code", mode="before")
    @classmethod
    def _normalize_session_code(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            return s if s else None
        return str(v)


class ExamSessionUpdate(BaseModel):
    session_code: Optional[str] = Field(None, min_length=1, max_length=64)
    enterprise_id: Optional[int] = Field(None, ge=1)
    course_id: Optional[int] = Field(None, ge=1)
    paper_id: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, max_length=200)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    status: Optional[str] = Field(None, description="draft|published|closed")


class ExamSessionOut(BaseModel):
    id: int
    session_code: str
    enterprise_id: int
    course_id: Optional[int] = None
    enterprise_name: Optional[str] = None
    course_name: Optional[str] = None
    paper_id: int
    paper_no: Optional[str] = Field(None, description="试卷编号")
    title: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    paper: Optional[PaperOut] = None

    model_config = {"from_attributes": True}
