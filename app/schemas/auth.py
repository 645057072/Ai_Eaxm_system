# -*- coding: utf-8 -*-

from typing import Optional

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


class UserMe(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    role: RoleBrief

    model_config = {"from_attributes": True}
