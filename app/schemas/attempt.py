# -*- coding: utf-8 -*-
"""作答与提交。"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnswerItemIn(BaseModel):
    question_id: int = Field(..., ge=1)
    user_answer_json: Any = None


class AnswersBatchIn(BaseModel):
    answers: List[AnswerItemIn] = Field(default_factory=list)


class ExamAnswerOut(BaseModel):
    id: int
    question_id: int
    user_answer_json: Optional[Any] = None
    score_awarded: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class ExamAttemptOut(BaseModel):
    id: int
    session_id: int
    user_id: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    status: str
    staged: bool = False
    practice_report: Optional[str] = Field(None, description="练习卷交卷后的文字报告")
    total_score: Optional[Decimal] = None
    answers: List[ExamAnswerOut] = []

    model_config = {"from_attributes": True}


class AttemptStartOut(BaseModel):
    attempt_id: int
    session_id: int
    paper_id: int
    duration_minutes: int
    started_at: datetime
    status: Optional[str] = None  # in_progress / submitted
    paper_type: str = "formal"
    staged: bool = False
