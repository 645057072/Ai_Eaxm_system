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


def is_enterprise_scope_admin(user: User) -> bool:
    """企业侧管理员：角色名称以「管理员」结尾时，在本企业及下级企业数据范围内拥有全部功能点（数据范围见 data_scope）。"""
    if user.role is None or not user.role.name:
        return False
    # 内置超管单独走 is_super_role，避免名称亦为「管理员」时重复判定
    if user.role.code == "admin":
        return False
    return user.role.name.strip().endswith("管理员")


def get_effective_codes(db: Session, user: User) -> Set[str]:
    if is_super_role(user):
        return set(ALL_CODES)
    if is_enterprise_scope_admin(user):
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
    if code.startswith("field.course.") and ("form.course" in granted or "list.course" in granted):
        return True
    if code.startswith("field.question.") and (
        "form.question" in granted
        or "list.question" in granted
        or "form.question_import" in granted
        or "form.question_batch" in granted
        or "action.question.manage" in granted
        or "action.question.import" in granted
        or "action.question.batch" in granted
    ):
        return True
    if code.startswith("field.paper.") and (
        "form.paper" in granted or "list.paper" in granted or "action.paper.manage" in granted
    ):
        return True
    if code.startswith("field.session.") and (
        "form.session" in granted or "list.session" in granted or "action.session.manage" in granted
    ):
        return True
    return False


def has_permission(db: Session, user: User, code: str) -> bool:
    if is_super_role(user):
        return True
    if is_enterprise_scope_admin(user):
        return True
    granted = get_effective_codes(db, user)
    return permission_match(granted, code)


def has_any_permission(db: Session, user: User, *codes: str) -> bool:
    return any(has_permission(db, user, c) for c in codes)
