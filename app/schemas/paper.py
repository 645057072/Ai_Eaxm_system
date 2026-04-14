# -*- coding: utf-8 -*-

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.question import QuestionOut


class PaperCompositionRule(BaseModel):
    """单条题型组卷规则：题库区间为关联课程下已发布题目。"""

    q_type: str = Field(..., min_length=1, max_length=16, description="题型 judge/single/multiple/fill")
    use_all: bool = Field(False, description="全选：该题型在题库区间内全部题目")
    count: int = Field(0, ge=0, description="抽题数量，全选时忽略")
    auto_split: int = Field(1, ge=1, description="自动拆分题目数量")
    score_per: Decimal = Field(Decimal("1"), ge=0, description="单题分值")

    @model_validator(mode="after")
    def _count_when_not_all(self) -> "PaperCompositionRule":
        if not self.use_all and self.count < 1:
            raise ValueError("未勾选「全选」时，抽题数量须至少为 1")
        return self


class PaperSummary(BaseModel):
    """列表用：不含小题明细。"""

    id: int
    title: str
    paper_no: Optional[str] = None
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    paper_type: str = "formal"
    level_id: Optional[int] = None
    level_name: Optional[str] = None
    enterprise_id: Optional[int] = None
    enterprise_name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: int
    total_score: Decimal
    item_count: int = Field(0, description="已组卷题目数量，大于0表示已组卷")
    session_ref_count: int = Field(0, description="引用该试卷的考试场次数量")
    audit_status: str = Field("draft", description="draft 草稿，reviewed 已审核")
    issue_date: Optional[date] = None
    valid_until: Optional[date] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaperCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    paper_no: Optional[str] = Field(None, max_length=64, description="为空则后端自动生成")
    course_id: Optional[int] = None
    paper_type: str = Field("formal", max_length=32)
    level_id: Optional[int] = None
    description: Optional[str] = None
    duration_minutes: int = Field(60, ge=1, le=600)
    issue_date: Optional[date] = Field(None, description="创建/签发日期")
    valid_until: Optional[date] = Field(None, description="有效期至（含当日仍有效；次日不可发布引用）")
    rules: List[PaperCompositionRule] = Field(default_factory=list, description="按题型抽题；空则仅创建空卷")

    @model_validator(mode="after")
    def _issue_valid_range(self) -> "PaperCreate":
        if self.issue_date and self.valid_until and self.valid_until < self.issue_date:
            raise ValueError("有效期不得早于创建日期")
        return self


class PaperUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    paper_no: Optional[str] = Field(None, max_length=64)
    course_id: Optional[int] = None
    paper_type: Optional[str] = Field(None, max_length=32)
    level_id: Optional[int] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    issue_date: Optional[date] = None
    valid_until: Optional[date] = None

    @model_validator(mode="after")
    def _issue_valid_range(self) -> "PaperUpdate":
        if self.issue_date and self.valid_until and self.valid_until < self.issue_date:
            raise ValueError("有效期不得早于创建日期")
        return self


class PaperItemOut(BaseModel):
    id: int
    question_id: int
    sort_order: int
    score: Decimal
    auto_split_count: int = 1
    question: Optional[QuestionOut] = None

    model_config = {"from_attributes": True}


class PaperOut(BaseModel):
    id: int
    title: str
    paper_no: Optional[str] = None
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    paper_type: str = "formal"
    level_id: Optional[int] = None
    level_name: Optional[str] = None
    composition_rules: Optional[Any] = None
    description: Optional[str] = None
    duration_minutes: int
    total_score: Decimal
    audit_status: str = "draft"
    issue_date: Optional[date] = None
    valid_until: Optional[date] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[PaperItemOut] = []

    model_config = {"from_attributes": True}


class PaperBatchIdsIn(BaseModel):
    """批量审核/反审核请求。"""

    ids: List[int] = Field(..., min_length=1)


class PaperItemAdd(BaseModel):
    question_id: int = Field(..., ge=1)
    sort_order: int = Field(0, ge=0)
    score: Decimal = Field(Decimal("1.00"), ge=Decimal("0"))
    auto_split_count: int = Field(1, ge=1)


class PaperBatchRule(BaseModel):
    """批量组卷：某题型在全部套卷中的题目总量（自动均分到各套）。"""

    q_type: str = Field(..., min_length=1, max_length=16)
    total_count: int = Field(..., ge=0)


class PaperBatchCreate(BaseModel):
    base_title: str = Field(..., min_length=1, max_length=200, description="试卷名称前缀；多套时自动加「第N套」")
    paper_count: int = Field(..., ge=1, le=50, description="生成试卷套数")
    course_id: int = Field(..., ge=1)
    paper_type: str = Field("formal", max_length=32)
    level_id: Optional[int] = None
    description: Optional[str] = None
    duration_minutes: int = Field(60, ge=1, le=600)
    rules: List[PaperBatchRule] = Field(..., min_length=1)
    auto_split: int = Field(1, ge=1)
    score_per: Decimal = Field(Decimal("1"), ge=0)
    issue_date: Optional[date] = Field(None, description="各套试卷统一的创建/签发日期")
    valid_until: Optional[date] = Field(None, description="各套试卷统一的有效期至")

    @model_validator(mode="after")
    def _nonzero_totals(self) -> "PaperBatchCreate":
        if sum(r.total_count for r in self.rules) < 1:
            raise ValueError("至少一种题型的总量须大于 0")
        qs = [r.q_type for r in self.rules if r.total_count > 0]
        if len(qs) != len(set(qs)):
            raise ValueError("同一题型只能配置一行（请合并题型总量）")
        if self.issue_date and self.valid_until and self.valid_until < self.issue_date:
            raise ValueError("有效期不得早于创建日期")
        return self


class PaperBatchOut(BaseModel):
    items: List[PaperSummary]
