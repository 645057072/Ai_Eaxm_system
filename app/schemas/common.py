# -*- coding: utf-8 -*-
"""分页与通用结构。"""

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    skip: int = Field(0, ge=0)
    # 用户管理等场景需一次拉取较多企业，上限放宽（仍防极端大包）
    limit: int = Field(20, ge=1, le=500)


class PageResult(BaseModel, Generic[T]):
    total: int
    items: List[T]
