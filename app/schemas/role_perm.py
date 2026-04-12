# -*- coding: utf-8 -*-

from typing import List

from pydantic import BaseModel, Field


class RolePermissionsIn(BaseModel):
    codes: List[str] = Field(default_factory=list)
