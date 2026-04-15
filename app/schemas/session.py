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
    attempt_limit: Optional[int] = Field(
        None,
        ge=1,
        description="模拟/正式卷答题次数上限；练习卷忽略（后端置空）。默认 1",
    )

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
    attempt_limit: Optional[int] = Field(None, ge=1, description="模拟/正式卷；练习卷后端置空")


class ExamSessionOut(BaseModel):
    id: int
    session_code: str
    enterprise_id: int
    course_id: Optional[int] = None
    enterprise_name: Optional[str] = None
    course_name: Optional[str] = None
    paper_id: int
    paper_no: Optional[str] = Field(None, description="试卷编号")
    paper_title: Optional[str] = Field(None, description="试卷档案中的试卷名称")
    paper_type: Optional[str] = Field(None, description="试卷类型 formal|mock|practice")
    attempt_limit: Optional[int] = Field(None, description="答题次数上限，空为不限制")
    title: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    status: str
    created_by: Optional[int] = None
    operator_name: Optional[str] = Field(None, description="新建场次操作员（用户名称）")
    published_by: Optional[int] = Field(None, description="发布人用户ID")
    publisher_name: Optional[str] = Field(None, description="发布员（用户名称）")
    created_at: datetime
    updated_at: datetime
    paper: Optional[PaperOut] = None

    model_config = {"from_attributes": True}
