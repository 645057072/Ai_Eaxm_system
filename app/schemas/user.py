# -*- coding: utf-8 -*-

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.auth import EnterpriseBrief, RoleBrief


class StudentBrief(BaseModel):
    id: int
    student_no: str
    full_name: str

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(None, max_length=64)
    role_id: int = Field(..., ge=1)
    # 可选；服务端以当前登录用户所属企业为准写入，防止跨企业建号
    enterprise_id: Optional[int] = Field(None, ge=1)
    student_id: Optional[int] = Field(None, ge=1, description="关联学员ID（一个用户只能关联一个学员）")
    enable_date: Optional[date] = Field(None, description="启用日期（默认当天）")
    expire_date: Optional[date] = Field(None, description="失效日期")


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=64)
    role_id: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    student_id: Optional[int] = Field(None, ge=1, description="关联学员ID（传 null 取消关联）")
    enable_date: Optional[date] = None
    expire_date: Optional[date] = None


class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    is_active: bool
    enterprise_id: Optional[int] = None
    enterprise: Optional[EnterpriseBrief] = None
    role: RoleBrief
    student_id: Optional[int] = None
    student: Optional[StudentBrief] = None
    enable_date: date
    expire_date: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}
