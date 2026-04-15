# -*- coding: utf-8 -*-

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class EnterpriseCreate(BaseModel):
    enterprise_code: str = Field(..., min_length=1, max_length=64, description="企业编码，全系统唯一")
    parent_id: Optional[int] = Field(None, ge=1, description="上级单位企业 ID，可为空")
    name: str = Field(..., min_length=1, max_length=200)
    tax_id: str = Field(..., min_length=1, max_length=32)
    address_phone: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=500)


class EnterpriseUpdate(BaseModel):
    enterprise_code: Optional[str] = Field(None, min_length=1, max_length=64)
    parent_id: Optional[int] = Field(None, description="上级单位；传 null 表示改为顶级（仅全局管理员）")
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    tax_id: Optional[str] = Field(None, min_length=1, max_length=32)
    address_phone: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=500)


class EnterpriseOut(BaseModel):
    id: int
    enterprise_code: str
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    name: str
    tax_id: str
    license_file_path: Optional[str] = None
    address_phone: Optional[str] = None
    contact_person: Optional[str] = None
    industry: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnterpriseTreeNode(EnterpriseOut):
    """树形展示用节点（含下级）。"""

    children: List["EnterpriseTreeNode"] = Field(default_factory=list)


EnterpriseTreeNode.model_rebuild()
