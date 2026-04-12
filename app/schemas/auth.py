# -*- coding: utf-8 -*-

from typing import List, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleBrief(BaseModel):
    id: int
    name: str
    code: str

    model_config = {"from_attributes": True}


class EnterpriseBrief(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class UserMe(BaseModel):
    """当前用户信息；permissions 为功能点编码列表，管理员为 [\"*\"] 表示全部。"""

    id: int
    username: str
    full_name: Optional[str] = None
    enterprise_id: int
    enterprise: EnterpriseBrief
    role: RoleBrief
    permissions: List[str]

    model_config = {"from_attributes": True}
