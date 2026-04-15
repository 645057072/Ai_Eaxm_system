# -*- coding: utf-8 -*-
"""企业信息维护与营业执照附件。"""

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.config import get_settings
from app.core.permissions import is_super_role
from app.models.enterprise import Enterprise
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.enterprise import EnterpriseCreate, EnterpriseOut, EnterpriseTreeNode, EnterpriseUpdate
from app.services.data_scope import (
    enterprise_is_under_ancestor,
    ensure_in_managed_enterprise_scope,
    get_managed_enterprise_ids,
)

router = APIRouter()

_LICENSE_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


def _upload_root() -> Path:
    p = Path(get_settings().upload_root)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _to_out_loaded(e: Enterprise) -> EnterpriseOut:
    parent_name = e.parent.name if e.parent is not None else None
    return EnterpriseOut(
        id=e.id,
        enterprise_code=e.enterprise_code,
        parent_id=e.parent_id,
        parent_name=parent_name,
        name=e.name,
        tax_id=e.tax_id,
        license_file_path=e.license_file_path,
        address_phone=e.address_phone,
        contact_person=e.contact_person,
        industry=e.industry,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


def _validate_parent_for_create(db: Session, current: User, parent_id: int | None) -> None:
    if is_super_role(current):
        if parent_id is not None and db.get(Enterprise, parent_id) is None:
            raise HTTPException(status_code=400, detail="上级单位不存在")
        return
    if parent_id is None:
        raise HTTPException(status_code=400, detail="非全局管理员新建企业须指定上级单位")
    ensure_in_managed_enterprise_scope(db, current, parent_id)


def _validate_parent_for_update(
    db: Session, current: User, enterprise_id: int, new_parent_id: int | None
) -> None:
    if new_parent_id is None:
        if not is_super_role(current):
            raise HTTPException(status_code=400, detail="仅全局管理员可将企业调整为无上级单位")
        return
    if new_parent_id == enterprise_id:
        raise HTTPException(status_code=400, detail="上级单位不能为自身")
    if db.get(Enterprise, new_parent_id) is None:
        raise HTTPException(status_code=400, detail="上级单位不存在")
    if enterprise_is_under_ancestor(db, enterprise_id, new_parent_id):
        raise HTTPException(status_code=400, detail="上级单位不能选择当前企业的下级单位")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, new_parent_id)


@router.get("/tree", response_model=list[EnterpriseTreeNode])
def list_enterprise_tree(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User,
        Depends(require_any_permission("list.enterprise", "list.question")),
    ],
) -> list[EnterpriseTreeNode]:
    """企业树：仅包含当前用户可管理范围内的企业；子节点不限层级。"""
    qry = select(Enterprise).options(joinedload(Enterprise.parent)).order_by(Enterprise.id.asc())
    if is_super_role(current):
        rows = db.scalars(qry).all()
    else:
        managed = get_managed_enterprise_ids(db, current)
        if not managed:
            return []
        qry = qry.where(Enterprise.id.in_(managed))
        rows = db.scalars(qry).all()

    by_id: dict[int, EnterpriseTreeNode] = {}
    for r in rows:
        o = _to_out_loaded(r)
        by_id[r.id] = EnterpriseTreeNode.model_validate({**o.model_dump(), "children": []})

    roots: list[EnterpriseTreeNode] = []
    for r in rows:
        node = by_id[r.id]
        pid = r.parent_id
        if pid is not None and pid in by_id:
            by_id[pid].children.append(node)
        else:
            roots.append(node)

    def sort_children(n: EnterpriseTreeNode) -> None:
        n.children.sort(key=lambda x: x.id)
        for c in n.children:
            sort_children(c)

    roots.sort(key=lambda x: x.id)
    for root in roots:
        sort_children(root)
    return roots


@router.get("", response_model=PageResult[EnterpriseOut])
def list_enterprises(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User,
        Depends(require_any_permission("list.enterprise", "list.question")),
    ],
    page: Annotated[PageParams, Depends()],
    keyword: str | None = Query(default=None, description="模糊匹配企业名称或编码"),
) -> PageResult[EnterpriseOut]:
    """企业档案：超管查看全部；企业管理员查看本企业及下级；其余用户仅本企业。"""
    q = (keyword or "").strip()
    kw_like = f"%{q}%" if q else None

    base = select(Enterprise).options(joinedload(Enterprise.parent))

    if is_super_role(current):
        stmt = select(func.count()).select_from(Enterprise)
        qry = base
        if kw_like is not None:
            stmt = stmt.where(
                Enterprise.name.like(kw_like) | Enterprise.enterprise_code.like(kw_like)
            )
            qry = qry.where(Enterprise.name.like(kw_like) | Enterprise.enterprise_code.like(kw_like))
        total = db.scalar(stmt) or 0
        rows = db.scalars(
            qry.offset(page.skip).limit(page.limit).order_by(Enterprise.id.desc())
        ).all()
    else:
        managed = get_managed_enterprise_ids(db, current)
        if not managed:
            return PageResult[EnterpriseOut](total=0, items=[])
        stmt = select(func.count()).select_from(Enterprise).where(Enterprise.id.in_(managed))
        qry = base.where(Enterprise.id.in_(managed))
        if kw_like is not None:
            stmt = stmt.where(
                Enterprise.name.like(kw_like) | Enterprise.enterprise_code.like(kw_like)
            )
            qry = qry.where(Enterprise.name.like(kw_like) | Enterprise.enterprise_code.like(kw_like))
        total = db.scalar(stmt) or 0
        rows = db.scalars(
            qry.offset(page.skip).limit(page.limit).order_by(Enterprise.id.desc())
        ).all()
    return PageResult[EnterpriseOut](total=int(total), items=[_to_out_loaded(r) for r in rows])


@router.post("", response_model=EnterpriseOut)
def create_enterprise(
    body: EnterpriseCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.enterprise.create"))],
) -> EnterpriseOut:
    """新建企业档案。"""
    code = body.enterprise_code.strip()
    if db.scalar(select(func.count()).select_from(Enterprise).where(Enterprise.enterprise_code == code)):
        raise HTTPException(status_code=400, detail="企业编码已存在")
    if db.scalar(select(func.count()).select_from(Enterprise).where(Enterprise.tax_id == body.tax_id)):
        raise HTTPException(status_code=400, detail="纳税人识别号已存在")

    _validate_parent_for_create(db, current, body.parent_id)

    e = Enterprise(
        enterprise_code=code,
        parent_id=body.parent_id,
        name=body.name.strip(),
        tax_id=body.tax_id.strip(),
        address_phone=body.address_phone,
        contact_person=body.contact_person,
        industry=body.industry,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    e = db.scalars(select(Enterprise).options(joinedload(Enterprise.parent)).where(Enterprise.id == e.id)).first()
    return _to_out_loaded(e)


@router.get("/{enterprise_id}", response_model=EnterpriseOut)
def get_enterprise(
    enterprise_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.enterprise"))],
) -> EnterpriseOut:
    ensure_in_managed_enterprise_scope(db, current, enterprise_id)
    e = db.scalars(
        select(Enterprise).options(joinedload(Enterprise.parent)).where(Enterprise.id == enterprise_id)
    ).first()
    if e is None:
        raise HTTPException(status_code=404, detail="企业不存在")
    return _to_out_loaded(e)


@router.patch("/{enterprise_id}", response_model=EnterpriseOut)
def update_enterprise(
    enterprise_id: int,
    body: EnterpriseUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.enterprise.update"))],
) -> EnterpriseOut:
    ensure_in_managed_enterprise_scope(db, current, enterprise_id)
    e = db.get(Enterprise, enterprise_id)
    if e is None:
        raise HTTPException(status_code=404, detail="企业不存在")

    data = body.model_dump(exclude_unset=True)
    if "parent_id" in data:
        new_p = data["parent_id"]
        _validate_parent_for_update(db, current, enterprise_id, new_p)
        e.parent_id = new_p

    if "enterprise_code" in data and data["enterprise_code"] is not None:
        nc = data["enterprise_code"].strip()
        if nc != e.enterprise_code:
            if db.scalar(
                select(func.count()).select_from(Enterprise).where(
                    Enterprise.enterprise_code == nc, Enterprise.id != e.id
                )
            ):
                raise HTTPException(status_code=400, detail="企业编码已存在")
            e.enterprise_code = nc

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
    e = db.scalars(
        select(Enterprise).options(joinedload(Enterprise.parent)).where(Enterprise.id == enterprise_id)
    ).first()
    return _to_out_loaded(e)


@router.delete("/{enterprise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enterprise(
    enterprise_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.enterprise.delete"))],
) -> None:
    ensure_in_managed_enterprise_scope(db, current, enterprise_id)
    e = db.get(Enterprise, enterprise_id)
    if e is None:
        raise HTTPException(status_code=404, detail="企业不存在")
    n_child = db.scalar(select(func.count()).select_from(Enterprise).where(Enterprise.parent_id == enterprise_id)) or 0
    if n_child > 0:
        raise HTTPException(status_code=400, detail="存在下级企业，无法删除")
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
    ensure_in_managed_enterprise_scope(db, current, enterprise_id)
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
    e2 = db.scalars(
        select(Enterprise).options(joinedload(Enterprise.parent)).where(Enterprise.id == enterprise_id)
    ).first()
    return _to_out_loaded(e2)
