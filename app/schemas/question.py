# -*- coding: utf-8 -*-
"""题库题目请求/响应。"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class QuestionCreate(BaseModel):
    q_type: str = Field(..., description="judge|single|multiple|fill")
    stem: str = Field(..., min_length=1, max_length=2000, description="题干，不含解析，最长2000字")
    options_json: Optional[Any] = None
    answer_json: Any = None
    analysis: Optional[str] = None
    difficulty: int = Field(1, ge=1, le=5)
    status: str = Field("draft", description="draft 草稿 | published 已发布；新建不可为 disabled，禁用仅能对已发布题目操作")
    course_id: Optional[int] = Field(None, ge=1)
    enterprise_id: Optional[int] = Field(None, ge=1)


class QuestionUpdate(BaseModel):
    q_type: Optional[str] = None
    stem: Optional[str] = Field(default=None, max_length=2000)
    options_json: Optional[Any] = None
    answer_json: Optional[Any] = None
    analysis: Optional[str] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = None
    course_id: Optional[int] = Field(None, ge=1)
    enterprise_id: Optional[int] = Field(None, ge=1)


class QuestionOut(BaseModel):
    id: int
    question_no: str
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


class QuestionBatchDeleteIn(BaseModel):
    """批量删除题目。"""

    ids: list[int] = Field(..., min_length=1)


class QuestionBatchDifficultyIn(BaseModel):
    """批量修改题目难度系数（1～5）。"""

    ids: list[int] = Field(..., min_length=1)
    difficulty: int = Field(..., ge=1, le=5)


class QuestionBatchIdsIn(BaseModel):
    """仅传题目 id 列表的批量操作入参。"""

    ids: list[int] = Field(..., min_length=1)


class QuestionImportResult(BaseModel):
    """题库导入结果。"""

    created: int
    skipped_duplicate: int = 0
    failed: int = 0
    by_type: dict[str, int] = Field(default_factory=dict, description="按题型统计成功导入数量")
    message: str
    log_text: str = Field("", description="导入明细日志，可下载留存")


class QuestionNeighborsOut(BaseModel):
    """与列表查询条件一致时的上一题/下一题 id（按 id 降序，与列表页相同）。"""

    prev_id: Optional[int] = Field(None, description="上一条（列表中更靠前，id 更大）")
    next_id: Optional[int] = Field(None, description="下一条（列表中更靠后，id 更小）")
    index: int = Field(..., description="当前题目在筛选结果中的下标，从 0 开始")
    total: int = Field(..., description="筛选结果总题数")
