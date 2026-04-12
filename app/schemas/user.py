# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.auth import EnterpriseBrief, RoleBrief


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(None, max_length=64)
    role_id: int = Field(..., ge=1)
    # 可选；服务端以当前登录用户所属企业为准写入，防止跨企业建号
    enterprise_id: Optional[int] = Field(None, ge=1)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=64)
    role_id: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    is_active: bool
    enterprise_id: int
    enterprise: EnterpriseBrief
    role: RoleBrief
    created_at: datetime

    model_config = {"from_attributes": True}
