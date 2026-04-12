# -*- coding: utf-8 -*-
"""功能点目录（供角色授权界面）。"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_permission
from app.core.permission_catalog import (
    catalog_action_groups,
    catalog_by_kind_sections,
    catalog_field_tag_groups,
    catalog_groups,
    catalog_mlf_tree,
)
from app.models.user import User

router = APIRouter()


@router.get("/catalog")
def get_permission_catalog(
    _: Annotated[User, Depends(require_permission("action.role.permission"))],
) -> dict:
    """功能点目录：groups 为扁平标签分组；byKind 为菜单/列表/表单/字段/操作分层，供弹窗授权。"""
    return {
        "groups": catalog_groups(),
        "byKind": catalog_by_kind_sections(),
        "treeMlf": catalog_mlf_tree(),
        "fieldGroups": catalog_field_tag_groups(),
        "actionGroups": catalog_action_groups(),
    }
