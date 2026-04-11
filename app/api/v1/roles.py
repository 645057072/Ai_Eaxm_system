# -*- coding: utf-8 -*-
"""角色列表（用于下拉框）。"""

from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import Role, User
from app.schemas.auth import RoleBrief

router = APIRouter()


@router.get("", response_model=List[RoleBrief])
def list_roles(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> List[RoleBrief]:
    """全部角色。"""
    rows = db.scalars(select(Role).order_by(Role.id.asc())).all()
    return [RoleBrief.model_validate(r) for r in rows]
