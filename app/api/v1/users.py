# -*- coding: utf-8 -*-

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_permission
from app.core.permissions import is_super_role
from app.core.security import hash_password
from app.models.enterprise import Enterprise
from app.models.user import Role, User
from app.schemas.common import PageParams, PageResult
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.data_scope import ensure_same_enterprise

router = APIRouter()


@router.get("", response_model=PageResult[UserOut])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.user"))],
    page: Annotated[PageParams, Depends()],
    keyword: str | None = None,
    enterprise_id: int | None = None,
) -> PageResult[UserOut]:
    """用户列表：非超管仅本企业；超管可查全部，可按 enterprise_id 筛选。"""
    stmt = select(func.count()).select_from(User)
    q = select(User).options(joinedload(User.enterprise), joinedload(User.role))
    if is_super_role(current):
        if enterprise_id is not None:
            stmt = stmt.where(User.enterprise_id == enterprise_id)
            q = q.where(User.enterprise_id == enterprise_id)
    else:
        if current.enterprise_id is None:
            return PageResult[UserOut](total=0, items=[])
        stmt = stmt.where(User.enterprise_id == current.enterprise_id)
        q = q.where(User.enterprise_id == current.enterprise_id)
    if keyword:
        stmt = stmt.where(User.username.like(f"%{keyword}%"))
        q = q.where(User.username.like(f"%{keyword}%"))
    total = db.scalar(stmt) or 0
    rows = db.scalars(q.offset(page.skip).limit(page.limit).order_by(User.id.desc())).all()
    return PageResult[UserOut](total=int(total), items=[UserOut.model_validate(r) for r in rows])


@router.post("", response_model=UserOut)
def create_user(
    body: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.user.create"))],
) -> UserOut:
    """在本企业创建用户；超管须指定 enterprise_id。"""
    if db.scalar(select(func.count()).select_from(User).where(User.username == body.username)):
        raise HTTPException(status_code=400, detail="用户名已存在")
    role = db.get(Role, body.role_id)
    if role is None:
        raise HTTPException(status_code=400, detail="角色不存在")
    if is_super_role(current):
        if body.enterprise_id is None:
            raise HTTPException(status_code=400, detail="请指定所属企业")
        if db.get(Enterprise, body.enterprise_id) is None:
            raise HTTPException(status_code=400, detail="企业不存在")
        eid = body.enterprise_id
    else:
        if current.enterprise_id is None:
            raise HTTPException(status_code=400, detail="当前账号未关联企业，无法创建用户")
        eid = current.enterprise_id
    u = User(
        username=body.username,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role_id=body.role_id,
        enterprise_id=eid,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    u = db.scalars(
        select(User).options(joinedload(User.enterprise), joinedload(User.role)).where(User.id == u.id)
    ).first()
    return UserOut.model_validate(u)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.user"))],
) -> UserOut:
    u = db.scalars(
        select(User).options(joinedload(User.enterprise), joinedload(User.role)).where(User.id == user_id)
    ).first()
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not is_super_role(current):
        ensure_same_enterprise(current, u.enterprise_id)
    return UserOut.model_validate(u)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.user.update"))],
) -> UserOut:
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not is_super_role(current):
        ensure_same_enterprise(current, u.enterprise_id)
    if body.full_name is not None:
        u.full_name = body.full_name
    if body.role_id is not None:
        if db.get(Role, body.role_id) is None:
            raise HTTPException(status_code=400, detail="角色不存在")
        u.role_id = body.role_id
    if body.is_active is not None:
        u.is_active = body.is_active
    if body.password:
        u.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(u)
    u = db.scalars(
        select(User).options(joinedload(User.enterprise), joinedload(User.role)).where(User.id == user_id)
    ).first()
    return UserOut.model_validate(u)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.user.delete"))],
) -> None:
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not is_super_role(current):
        ensure_same_enterprise(current, u.enterprise_id)
    db.delete(u)
    db.commit()
