# -*- coding: utf-8 -*-
"""依赖注入：数据库、当前用户、角色校验。"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.permissions import has_any_permission, has_permission
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)


def get_current_user_optional(
    db: Annotated[Session, Depends(get_db)],
    cred: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> Optional[User]:
    if cred is None or cred.credentials is None:
        return None
    payload = decode_token(cred.credentials)
    if not payload or "sub" not in payload:
        return None
    uid = int(payload["sub"])
    user = db.get(User, uid)
    if user is None or not user.is_active:
        return None
    return user


def get_current_user(
    user: Annotated[Optional[User], Depends(get_current_user_optional)],
) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或令牌无效")
    return user


def require_roles(*codes: str):
    """要求当前用户角色 code 在允许列表内。"""

    def _inner(user: Annotated[User, Depends(get_current_user)]) -> User:
        rcode = user.role.code if user.role else ""
        if rcode not in codes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return user

    return _inner


def require_permission(code: str):
    """要求具备指定功能点（管理员角色不受限）。"""

    def _inner(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        if not has_permission(db, user, code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无访问权限")
        return user

    return _inner


def require_any_permission(*codes: str):
    """具备任一功能点即可。"""

    def _inner(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        if not has_any_permission(db, user, *codes):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无访问权限")
        return user

    return _inner
