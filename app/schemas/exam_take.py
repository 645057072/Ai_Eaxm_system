# -*- coding: utf-8 -*-
"""考生端可见题目（不含标准答案）。"""

from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class TakeQuestionItem(BaseModel):
    question_id: int
    q_type: str
    stem: str
    options_json: Optional[Any] = None
    score: Decimal


class TakeDataOut(BaseModel):
    session_id: int
    title: str
    paper_id: int
    paper_type: str = "formal"
    duration_minutes: int
    questions: List[TakeQuestionItem] = Field(default_factory=list)
