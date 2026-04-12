# -*- coding: utf-8 -*-
"""功能点匹配与角色授权加载。"""

from typing import Set

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permission_catalog import ALL_CODES
from app.models.permission import RolePermission
from app.models.user import User


def is_super_role(user: User) -> bool:
    """内置管理员角色拥有全部功能点（与库中授权无关）。"""
    return bool(user.role and user.role.code == "admin")


def get_effective_codes(db: Session, user: User) -> Set[str]:
    if is_super_role(user):
        return set(ALL_CODES)
    rows = db.scalars(
        select(RolePermission.permission_code).where(RolePermission.role_id == user.role_id)
    ).all()
    return set(rows)


def permission_match(granted: Set[str], code: str) -> bool:
    """是否允许访问某功能点（含前缀继承与表单-字段规则）。"""
    if code in granted:
        return True
    for g in granted:
        if code.startswith(g + "."):
            return True
    if code.startswith("field.user.") and "form.user" in granted:
        return True
    if code.startswith("field.enterprise.") and "form.enterprise" in granted:
        return True
    return False


def has_permission(db: Session, user: User, code: str) -> bool:
    if is_super_role(user):
        return True
    granted = get_effective_codes(db, user)
    return permission_match(granted, code)


def has_any_permission(db: Session, user: User, *codes: str) -> bool:
    return any(has_permission(db, user, c) for c in codes)
