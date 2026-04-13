# -*- coding: utf-8 -*-

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    code: str = Field(..., min_length=1, max_length=32)
    description: Optional[str] = Field(None, max_length=255)

    @field_validator("code")
    @classmethod
    def normalize_role_code(cls, v: str) -> str:
        # 去掉首尾空白并统一小写，避免前端大小写混用导致校验 422
        s = v.strip().lower()
        if not s:
            raise ValueError("请填写角色编码")
        if not re.match(r"^[a-z][a-z0-9_]*$", s):
            raise ValueError("角色编码须为小写字母开头，仅含小写字母、数字、下划线")
        return s


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=255)


class RoleOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    created_at: datetime
    user_count: int = 0

    model_config = {"from_attributes": True}
