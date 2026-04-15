# -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ExamServiceRecordOut(BaseModel):
    id: int
    attempt_id: int
    enterprise_id: int
    exam_no: str = Field(..., description="考试编号（场次编码）")
    course_name: str
    paper_title: str
    enterprise_name: str
    student_display: str
    score: Decimal
    passed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
