# -*- coding: utf-8 -*-
"""考试场次。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.paper import PaperOut


class ExamSessionCreate(BaseModel):
    paper_id: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class ExamSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    status: Optional[str] = Field(None, description="draft|published|closed")


class ExamSessionOut(BaseModel):
    id: int
    paper_id: int
    title: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    paper: Optional[PaperOut] = None

    model_config = {"from_attributes": True}
