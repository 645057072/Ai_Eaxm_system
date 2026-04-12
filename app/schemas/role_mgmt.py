# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    code: str = Field(..., min_length=1, max_length=32, pattern=r"^[a-z][a-z0-9_]*$")
    description: Optional[str] = Field(None, max_length=255)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=255)


class RoleOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
