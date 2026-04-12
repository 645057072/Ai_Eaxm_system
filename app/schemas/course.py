# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.auth import EnterpriseBrief


class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    instructor: str = Field(..., min_length=1, max_length=100)
    period_text: str = Field(..., min_length=1, max_length=255, description="课程期间")
    description: Optional[str] = Field(None, max_length=4000)
    enterprise_id: Optional[int] = Field(None, ge=1, description="超管创建时指定企业")


class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    instructor: Optional[str] = Field(None, min_length=1, max_length=100)
    period_text: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=4000)


class CourseOut(BaseModel):
    id: int
    name: str
    instructor: str
    period_text: str
    description: Optional[str] = None
    enterprise_id: int
    enterprise: EnterpriseBrief
    created_at: datetime

    model_config = {"from_attributes": True}
