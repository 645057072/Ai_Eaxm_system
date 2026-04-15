# -*- coding: utf-8 -*-
"""打印模板。"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class PrintTemplateCreate(BaseModel):
    template_no: str = Field(..., min_length=1, max_length=64, description="模板编号")
    template_name: str = Field("", max_length=200)
    module_code: str = Field(..., min_length=1, max_length=64, description="业务模块编码")
    menu_code: str = Field(..., min_length=1, max_length=128, description="关联菜单功能点")
    course_id: int = Field(..., ge=1)
    paper_format: str = Field("A4", max_length=32, description="A4|A3|B5|CUSTOM")


class PrintTemplateUpdate(BaseModel):
    template_name: Optional[str] = Field(None, max_length=200)
    module_code: Optional[str] = Field(None, max_length=64)
    menu_code: Optional[str] = Field(None, max_length=128)
    course_id: Optional[int] = Field(None, ge=1)
    paper_format: Optional[str] = Field(None, max_length=32)
    layout_json: Optional[dict[str, Any]] = None


class PrintTemplatePublishBody(BaseModel):
    """发布：指定 enterprise_id 则仅该企业下可用；不指定则全系统可用。"""

    enterprise_id: Optional[int] = Field(None, ge=1, description="所属企业；不传表示全局可用")


class PrintTemplateOut(BaseModel):
    id: int
    template_no: str
    template_name: str
    module_code: str
    menu_code: str
    course_id: int
    course_name: Optional[str] = None
    paper_format: str
    layout_json: dict[str, Any]
    publish_scope_enterprise_id: Optional[int] = None
    publish_scope_enterprise_name: Optional[str] = None
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
