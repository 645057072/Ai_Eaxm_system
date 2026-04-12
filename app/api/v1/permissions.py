# -*- coding: utf-8 -*-
"""功能点目录（供角色授权界面）。"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_permission
from app.core.permission_catalog import catalog_groups
from app.models.user import User

router = APIRouter()


@router.get("/catalog")
def get_permission_catalog(
    _: Annotated[User, Depends(require_permission("action.role.permission"))],
) -> dict:
    """按标签分组的功能点目录。"""
    return {"groups": catalog_groups()}
