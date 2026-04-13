# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PaperLevelCreate(BaseModel):
    level_code: str = Field(..., min_length=1, max_length=64, description="等级编号")
    level_name: str = Field(..., min_length=1, max_length=200, description="等级名称")
    title_series: str = Field(..., min_length=1, max_length=200, description="职称系列")
    enterprise_id: Optional[int] = Field(None, description="仅系统管理员创建时必填：所属企业")


class PaperLevelUpdate(BaseModel):
    level_code: Optional[str] = Field(None, max_length=64)
    level_name: Optional[str] = Field(None, max_length=200)
    title_series: Optional[str] = Field(None, max_length=200)


class PaperLevelOut(BaseModel):
    id: int
    level_code: str
    level_name: str
    title_series: str
    enterprise_id: int
    enterprise_name: Optional[str] = None
    created_by: Optional[int] = None
    operator_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
