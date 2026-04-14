# -*- coding: utf-8 -*-

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core.permissions import get_effective_codes, is_super_role
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import EnterpriseBrief, LoginRequest, MePasswordChange, RoleBrief, TokenResponse, UserMe

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """用户名密码登录，返回 JWT。"""
    user = db.scalars(select(User).where(User.username == body.username)).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")
    if user.expire_date is not None and date.today() > user.expire_date:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已失效，请联系管理员")
    token = create_access_token(user.id, extra={"role": user.role.code if user.role else ""})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserMe)
def me(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> UserMe:
    """当前登录用户信息（含所属企业与功能点）。"""
    u = db.scalars(
        select(User).options(joinedload(User.enterprise), joinedload(User.role)).where(User.id == current.id)
    ).first()
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if not is_super_role(u) and (u.enterprise_id is None or u.enterprise is None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户未关联企业")
    perms = ["*"] if is_super_role(u) else sorted(get_effective_codes(db, u))
    ent = (
        EnterpriseBrief(id=u.enterprise.id, name=u.enterprise.name)
        if u.enterprise is not None
        else None
    )
    return UserMe(
        id=u.id,
        username=u.username,
        full_name=u.full_name,
        enterprise_id=u.enterprise_id,
        enterprise=ent,
        role=RoleBrief.model_validate(u.role),
        permissions=perms,
    )


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    body: MePasswordChange,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> None:
    """当前用户修改密码。"""
    if not verify_password(body.old_password, current.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码错误")
    u = db.get(User, current.id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    u.password_hash = hash_password(body.new_password)
    db.commit()
