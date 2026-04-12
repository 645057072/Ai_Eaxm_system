# -*- coding: utf-8 -*-
"""角色列表与维护。"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import Role, User
from app.schemas.auth import RoleBrief
from app.schemas.role_mgmt import RoleCreate, RoleOut, RoleUpdate

router = APIRouter()

# 内置角色编码不可删除，避免系统无法登录或权限缺失
_RESERVED_ROLE_CODES = frozenset({"admin", "teacher", "student"})


@router.get("", response_model=List[RoleOut])
def list_roles(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> List[RoleOut]:
    """全部角色（含说明，供下拉与权限页）。"""
    rows = db.scalars(select(Role).order_by(Role.id.asc())).all()
    return [RoleOut.model_validate(r) for r in rows]


@router.post("", response_model=RoleOut)
def create_role(
    body: RoleCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin"))],
) -> RoleOut:
    if body.code in _RESERVED_ROLE_CODES:
        raise HTTPException(status_code=400, detail="该角色编码为系统保留")
    if db.scalar(select(func.count()).select_from(Role).where(Role.code == body.code)):
        raise HTTPException(status_code=400, detail="角色编码已存在")
    r = Role(name=body.name, code=body.code, description=body.description)
    db.add(r)
    db.commit()
    db.refresh(r)
    return RoleOut.model_validate(r)


@router.patch("/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int,
    body: RoleUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin"))],
) -> RoleOut:
    r = db.get(Role, role_id)
    if r is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    if body.name is not None:
        r.name = body.name
    if body.description is not None:
        r.description = body.description
    db.commit()
    db.refresh(r)
    return RoleOut.model_validate(r)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin"))],
) -> None:
    r = db.get(Role, role_id)
    if r is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    if r.code in _RESERVED_ROLE_CODES:
        raise HTTPException(status_code=400, detail="系统内置角色不可删除")
    n = db.scalar(select(func.count()).select_from(User).where(User.role_id == role_id)) or 0
    if n > 0:
        raise HTTPException(status_code=400, detail="仍有用户绑定该角色，无法删除")
    db.delete(r)
    db.commit()
