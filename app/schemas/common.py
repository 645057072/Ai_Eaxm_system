# -*- coding: utf-8 -*-
"""分页与通用结构。"""

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=200)


class PageResult(BaseModel, Generic[T]):
    total: int
    items: List[T]
