# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExamCandidateOut(BaseModel):
    id: int
    exam_no: str
    enterprise_id: int
    enterprise_name: Optional[str] = None
    course_id: int
    course_name: Optional[str] = None
    student_id: int
    student_no: Optional[str] = None
    student_name: Optional[str] = None
    session_id: Optional[int] = None
    last_attempt_id: Optional[int] = None
    answer_duration_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExamCandidateCreate(BaseModel):
    exam_no: str = Field(..., min_length=1, max_length=64)
    enterprise_id: Optional[int] = Field(None, description="超管必填；企业用户可省略")
    course_id: int
    student_id: int


class ExamCandidateUpdate(BaseModel):
    exam_no: Optional[str] = Field(None, max_length=64)
    enterprise_id: Optional[int] = None
    course_id: Optional[int] = None
    student_id: Optional[int] = None
