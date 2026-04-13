# -*- coding: utf-8 -*-
"""角色列表与维护、功能授权。"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.permission_catalog import ALL_CODES
from app.models.permission import RolePermission
from app.models.user import Role, User
from app.schemas.role_mgmt import RoleCreate, RoleOut, RoleUpdate
from app.schemas.role_perm import RolePermissionsIn

router = APIRouter()

_RESERVED_ROLE_CODES = frozenset({"admin", "teacher", "student"})


@router.get("", response_model=List[RoleOut])
def list_roles(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_any_permission("list.role", "action.user.create", "action.user.update")),
    ],
) -> List[RoleOut]:
    """全部角色（角色管理页或用户表单下拉）；user_count 为绑定该角色的用户数。"""
    rows = db.scalars(select(Role).order_by(Role.id.asc())).all()
    out: List[RoleOut] = []
    for r in rows:
        n = int(db.scalar(select(func.count()).select_from(User).where(User.role_id == r.id)) or 0)
        base = RoleOut.model_validate(r)
        out.append(base.model_copy(update={"user_count": n}))
    return out


@router.get("/{role_id}", response_model=RoleOut)
def get_role(
    role_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_any_permission("list.role", "action.role.permission", "action.role.update")),
    ],
) -> RoleOut:
    """单条角色（功能授权内页标题等）。"""
    r = db.get(Role, role_id)
    if r is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    n = int(db.scalar(select(func.count()).select_from(User).where(User.role_id == role_id)) or 0)
    base = RoleOut.model_validate(r)
    return base.model_copy(update={"user_count": n})


@router.post("", response_model=RoleOut)
def create_role(
    body: RoleCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("action.role.create"))],
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


@router.get("/{role_id}/permissions", response_model=List[str])
def get_role_permissions(
    role_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[
        User,
        Depends(
            require_any_permission(
                "action.role.permission",
                "action.user.create",
                "action.user.update",
            )
        ),
    ],
) -> List[str]:
    """查询某角色已授权的功能点编码。"""
    if db.get(Role, role_id) is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    rows = db.scalars(select(RolePermission.permission_code).where(RolePermission.role_id == role_id)).all()
    return list(rows)


@router.put("/{role_id}/permissions", response_model=List[str])
def set_role_permissions(
    role_id: int,
    body: RolePermissionsIn,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("action.role.permission"))],
) -> List[str]:
    """覆盖写入角色功能授权。"""
    r = db.get(Role, role_id)
    if r is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    valid = set(ALL_CODES)
    for c in body.codes:
        if c not in valid:
            raise HTTPException(status_code=400, detail=f"未知功能点: {c}")
    db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    for c in body.codes:
        db.add(RolePermission(role_id=role_id, permission_code=c))
    db.commit()
    rows = db.scalars(select(RolePermission.permission_code).where(RolePermission.role_id == role_id)).all()
    return list(rows)


@router.patch("/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int,
    body: RoleUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("action.role.update"))],
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
    n = int(db.scalar(select(func.count()).select_from(User).where(User.role_id == role_id)) or 0)
    base = RoleOut.model_validate(r)
    return base.model_copy(update={"user_count": n})


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("action.role.delete"))],
) -> None:
    r = db.get(Role, role_id)
    if r is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    if r.code in _RESERVED_ROLE_CODES:
        raise HTTPException(status_code=400, detail="系统内置角色不可删除")
    n = db.scalar(select(func.count()).select_from(User).where(User.role_id == role_id)) or 0
    if n > 0:
        raise HTTPException(status_code=400, detail="仍有用户绑定该角色，无法删除")
    db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    db.delete(r)
    db.commit()
