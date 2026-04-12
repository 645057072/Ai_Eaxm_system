# -*- coding: utf-8 -*-
"""题库题目请求/响应。"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class QuestionCreate(BaseModel):
    q_type: str = Field(..., description="judge|single|multiple|fill")
    stem: str = Field(..., min_length=1)
    options_json: Optional[Any] = None
    answer_json: Any = None
    analysis: Optional[str] = None
    difficulty: int = Field(1, ge=1, le=5)
    status: str = Field("draft", description="draft|published")
    course_id: Optional[int] = Field(None, ge=1)
    enterprise_id: Optional[int] = Field(None, ge=1)


class QuestionUpdate(BaseModel):
    q_type: Optional[str] = None
    stem: Optional[str] = None
    options_json: Optional[Any] = None
    answer_json: Optional[Any] = None
    analysis: Optional[str] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = None
    course_id: Optional[int] = Field(None, ge=1)
    enterprise_id: Optional[int] = Field(None, ge=1)


class QuestionOut(BaseModel):
    id: int
    q_type: str
    stem: str
    options_json: Optional[Any] = None
    answer_json: Any = None
    analysis: Optional[str] = None
    difficulty: int
    status: str
    course_id: Optional[int] = None
    enterprise_id: Optional[int] = None
    course_name: Optional[str] = None
    enterprise_name: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuestionBatchPublishIn(BaseModel):
    """批量将题目状态改为已发布。"""

    ids: list[int] = Field(..., min_length=1)


class QuestionImportResult(BaseModel):
    """题库导入结果。"""

    created: int
    message: str
