# -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.question import QuestionOut


class PaperSummary(BaseModel):
    """列表用：不含小题明细。"""

    id: int
    title: str
    description: Optional[str] = None
    duration_minutes: int
    total_score: Decimal
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaperCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    duration_minutes: int = Field(60, ge=1, le=600)


class PaperUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)


class PaperItemOut(BaseModel):
    id: int
    question_id: int
    sort_order: int
    score: Decimal
    question: Optional[QuestionOut] = None

    model_config = {"from_attributes": True}


class PaperOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    duration_minutes: int
    total_score: Decimal
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[PaperItemOut] = []

    model_config = {"from_attributes": True}


class PaperItemAdd(BaseModel):
    question_id: int = Field(..., ge=1)
    sort_order: int = Field(0, ge=0)
    score: Decimal = Field(Decimal("1.00"), ge=Decimal("0"))
