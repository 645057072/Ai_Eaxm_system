# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StudentOut(BaseModel):
    id: int
    student_no: str
    full_name: str
    gender: Optional[str] = None
    birth_month: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    id_card_no: Optional[str] = None
    address_phone: Optional[str] = None
    remark: Optional[str] = None
    enterprise_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StudentCreate(BaseModel):
    student_no: str = Field(..., min_length=1, max_length=64)
    full_name: str = Field(..., min_length=1, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    birth_month: Optional[str] = Field(None, max_length=7, description="YYYY-MM")
    company_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    id_card_no: Optional[str] = Field(None, max_length=32)
    address_phone: Optional[str] = Field(None, max_length=500)
    remark: Optional[str] = None
    enterprise_id: Optional[int] = Field(None, description="超管可指定；普通用户忽略")


class StudentUpdate(BaseModel):
    student_no: Optional[str] = Field(None, max_length=64)
    full_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    birth_month: Optional[str] = Field(None, max_length=7)
    company_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    id_card_no: Optional[str] = Field(None, max_length=32)
    address_phone: Optional[str] = Field(None, max_length=500)
    remark: Optional[str] = None
    enterprise_id: Optional[int] = None

