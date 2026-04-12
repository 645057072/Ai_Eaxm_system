# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EnterpriseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    tax_id: str = Field(..., min_length=1, max_length=32)
    address_phone: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=500)


class EnterpriseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    tax_id: Optional[str] = Field(None, min_length=1, max_length=32)
    address_phone: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=500)


class EnterpriseOut(BaseModel):
    id: int
    name: str
    tax_id: str
    license_file_path: Optional[str] = None
    address_phone: Optional[str] = None
    contact_person: Optional[str] = None
    industry: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
