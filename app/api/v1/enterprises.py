# -*- coding: utf-8 -*-
"""企业信息维护与营业执照附件。"""

import re
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.permissions import is_super_role
from app.core.config import get_settings
from app.models.enterprise import Enterprise
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.enterprise import EnterpriseCreate, EnterpriseOut, EnterpriseUpdate
from app.services.data_scope import ensure_same_enterprise

router = APIRouter()

_LICENSE_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


def _upload_root() -> Path:
    p = Path(get_settings().upload_root)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.get("", response_model=PageResult[EnterpriseOut])
def list_enterprises(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User,
        Depends(require_any_permission("list.enterprise", "list.question")),
    ],
    page: Annotated[PageParams, Depends()],
    keyword: Annotated[str | None, Query(description="模糊匹配企业名称")] = None,
) -> PageResult[EnterpriseOut]:
    """企业档案：超管查看全部；其余用户仅本企业。支持 keyword 模糊搜索。"""
    q = (keyword or "").strip()
    kw_like = f"%{q}%" if q else None

    if is_super_role(current):
        stmt = select(func.count()).select_from(Enterprise)
        qry = select(Enterprise)
        if kw_like is not None:
            stmt = stmt.where(Enterprise.name.like(kw_like))
            qry = qry.where(Enterprise.name.like(kw_like))
        total = db.scalar(stmt) or 0
        rows = db.scalars(
            qry.offset(page.skip).limit(page.limit).order_by(Enterprise.id.desc())
        ).all()
    else:
        if current.enterprise_id is None:
            return PageResult[EnterpriseOut](total=0, items=[])
        stmt = select(func.count()).select_from(Enterprise).where(Enterprise.id == current.enterprise_id)
        qry = select(Enterprise).where(Enterprise.id == current.enterprise_id)
        if kw_like is not None:
            stmt = stmt.where(Enterprise.name.like(kw_like))
            qry = qry.where(Enterprise.name.like(kw_like))
        total = db.scalar(stmt) or 0
        rows = db.scalars(
            qry.offset(page.skip).limit(page.limit).order_by(Enterprise.id.desc())
        ).all()
    return PageResult[EnterpriseOut](total=int(total), items=[EnterpriseOut.model_validate(r) for r in rows])


@router.post("", response_model=EnterpriseOut)
def create_enterprise(
    body: EnterpriseCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("action.enterprise.create"))],
) -> EnterpriseOut:
    """新建企业档案（多租户扩容用）。"""
    if db.scalar(select(func.count()).select_from(Enterprise).where(Enterprise.tax_id == body.tax_id)):
        raise HTTPException(status_code=400, detail="纳税人识别号已存在")
    e = Enterprise(
        name=body.name,
        tax_id=body.tax_id,
        address_phone=body.address_phone,
        contact_person=body.contact_person,
        industry=body.industry,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return EnterpriseOut.model_validate(e)


@router.get("/{enterprise_id}", response_model=EnterpriseOut)
def get_enterprise(
    enterprise_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.enterprise"))],
) -> EnterpriseOut:
    ensure_same_enterprise(current, enterprise_id)
    e = db.get(Enterprise, enterprise_id)
    if e is None:
        raise HTTPException(status_code=404, detail="企业不存在")
    return EnterpriseOut.model_validate(e)


@router.patch("/{enterprise_id}", response_model=EnterpriseOut)
def update_enterprise(
    enterprise_id: int,
    body: EnterpriseUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.enterprise.update"))],
) -> EnterpriseOut:
    ensure_same_enterprise(current, enterprise_id)
    e = db.get(Enterprise, enterprise_id)
    if e is None:
        raise HTTPException(status_code=404, detail="企业不存在")
    if body.tax_id is not None and body.tax_id != e.tax_id:
        if db.scalar(
            select(func.count()).select_from(Enterprise).where(Enterprise.tax_id == body.tax_id, Enterprise.id != e.id)
        ):
            raise HTTPException(status_code=400, detail="纳税人识别号已存在")
        e.tax_id = body.tax_id
    if body.name is not None:
        e.name = body.name
    if body.address_phone is not None:
        e.address_phone = body.address_phone
    if body.contact_person is not None:
        e.contact_person = body.contact_person
    if body.industry is not None:
        e.industry = body.industry
    db.commit()
    db.refresh(e)
    return EnterpriseOut.model_validate(e)


@router.delete("/{enterprise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enterprise(
    enterprise_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.enterprise.delete"))],
) -> None:
    ensure_same_enterprise(current, enterprise_id)
    e = db.get(Enterprise, enterprise_id)
    if e is None:
        raise HTTPException(status_code=404, detail="企业不存在")
    n = db.scalar(select(func.count()).select_from(User).where(User.enterprise_id == enterprise_id)) or 0
    if n > 0:
        raise HTTPException(status_code=400, detail="仍有用户归属该企业，无法删除")
    if e.license_file_path:
        fp = _upload_root() / e.license_file_path
        if fp.is_file():
            fp.unlink()
    db.delete(e)
    db.commit()


@router.post("/{enterprise_id}/license", response_model=EnterpriseOut)
async def upload_license(
    enterprise_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.enterprise.update"))],
    file: UploadFile = File(...),
) -> EnterpriseOut:
    ensure_same_enterprise(current, enterprise_id)
    e = db.get(Enterprise, enterprise_id)
    if e is None:
        raise HTTPException(status_code=404, detail="企业不存在")
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")
    ext = Path(file.filename).suffix.lower()
    if ext not in _LICENSE_EXT:
        raise HTTPException(status_code=400, detail="仅支持 pdf/jpg/png/webp")
    root = _upload_root()
    new_name = f"ent_{enterprise_id}_{uuid.uuid4().hex}{ext}"
    dest = root / new_name
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件超过 10MB")
    if e.license_file_path:
        old = root / e.license_file_path
        if old.is_file():
            old.unlink()
    dest.write_bytes(content)
    e.license_file_path = new_name
    db.commit()
    db.refresh(e)
    return EnterpriseOut.model_validate(e)
