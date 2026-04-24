# -*- coding: utf-8 -*-
"""证书模板与颁发记录 Schema。"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field


class CertTemplateCreate(BaseModel):
    enterprise_id: int | None = Field(default=None, description="所属企业；非超管忽略，取当前用户企业")
    cert_code: str = Field(..., min_length=1, max_length=64, description="模板编码")
    name: str = Field(default="", max_length=200)
    course_id: int | None = Field(default=None, description="关联课程 ID，空为通用")
    layout_json: dict[str, Any] | None = Field(default=None, description="版式 JSON，空则用默认")
    status: str = Field(default="draft", max_length=16, description="draft|published")


class CertTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    course_id: int | None = None
    layout_json: dict[str, Any] | None = None
    status: str | None = Field(default=None, max_length=16)


class CertTemplateOut(BaseModel):
    id: int
    enterprise_id: int
    enterprise_name: str | None = None
    cert_code: str
    name: str
    course_id: int | None
    course_name: str | None = None
    layout_json: dict[str, Any]
    status: str
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CertRecordOut(BaseModel):
    id: int
    enterprise_id: int
    certificate_no: str
    cert_template_id: int
    template_name: str | None = None
    cert_code: str | None = None
    user_id: int
    user_username: str | None = None
    exam_service_record_id: int
    exam_no: str | None = None
    student_display: str
    course_name: str
    paper_title: str
    score: Decimal | None
    passed: bool | None
    issued_at: datetime
    issued_by: int | None
    issuer_name: str | None = None

    model_config = {"from_attributes": True}


class CertRecordIssueBody(BaseModel):
    exam_service_record_id: int = Field(..., ge=1)
    cert_template_id: int = Field(..., ge=1)
    require_passed: bool = Field(default=True, description="为真时仅允许已通过考试记录颁发")
