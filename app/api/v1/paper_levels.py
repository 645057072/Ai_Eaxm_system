# -*- coding: utf-8 -*-
"""试卷等级 CRUD（按企业数据范围）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_permission
from app.core.permissions import is_super_role
from app.models.enterprise import Enterprise
from app.models.paper_level import PaperLevel
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.paper_level import PaperLevelCreate, PaperLevelOut, PaperLevelUpdate
from app.services.data_scope import ensure_in_managed_enterprise_scope, get_managed_enterprise_ids

router = APIRouter()


def _out_from_row(db: Session, row: PaperLevel) -> PaperLevelOut:
    ent_name = row.enterprise.name if row.enterprise else None
    op_name = None
    if row.created_by:
        u = db.get(User, row.created_by)
        op_name = u.username if u else None
    return PaperLevelOut(
        id=row.id,
        level_code=row.level_code,
        level_name=row.level_name,
        title_series=row.title_series,
        enterprise_id=row.enterprise_id,
        enterprise_name=ent_name,
        created_by=row.created_by,
        operator_name=op_name,
        created_at=row.created_at,
    )


@router.get("", response_model=PageResult[PaperLevelOut])
def list_paper_levels(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.paper_level"))],
    page: Annotated[PageParams, Depends()],
    keyword: str | None = Query(default=None, description="编号、名称、职称系列"),
    enterprise_id: int | None = Query(default=None, description="超管按企业筛选"),
) -> PageResult[PaperLevelOut]:
    """试卷等级列表。"""
    if not is_super_role(current) and current.enterprise_id is None:
        return PageResult[PaperLevelOut](total=0, items=[])

    q = (keyword or "").strip()
    kw_like = f"%{q}%" if q else None

    conds: list = []
    if not is_super_role(current):
        managed = get_managed_enterprise_ids(db, current)
        if not managed:
            return PageResult[PaperLevelOut](total=0, items=[])
        if enterprise_id is not None:
            if enterprise_id not in managed:
                return PageResult[PaperLevelOut](total=0, items=[])
            conds.append(PaperLevel.enterprise_id == enterprise_id)
        else:
            conds.append(PaperLevel.enterprise_id.in_(managed))
    elif enterprise_id is not None:
        conds.append(PaperLevel.enterprise_id == enterprise_id)
    if kw_like is not None:
        conds.append(
            or_(
                PaperLevel.level_code.like(kw_like),
                PaperLevel.level_name.like(kw_like),
                PaperLevel.title_series.like(kw_like),
            )
        )

    base = select(PaperLevel).join(Enterprise, PaperLevel.enterprise_id == Enterprise.id)
    cnt = select(func.count()).select_from(PaperLevel).join(Enterprise, PaperLevel.enterprise_id == Enterprise.id)
    if conds:
        w = and_(*conds)
        base = base.where(w)
        cnt = cnt.where(w)

    total = db.scalar(cnt) or 0
    rows = db.scalars(
        base.options(joinedload(PaperLevel.enterprise))
        .offset(page.skip)
        .limit(page.limit)
        .order_by(PaperLevel.id.desc())
    ).all()
    return PageResult[PaperLevelOut](total=int(total), items=[_out_from_row(db, r) for r in rows])


@router.post("", response_model=PaperLevelOut)
def create_paper_level(
    body: PaperLevelCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper_level.manage"))],
) -> PaperLevelOut:
    """新建试卷等级。"""
    if is_super_role(current):
        if body.enterprise_id is None:
            raise HTTPException(status_code=400, detail="请选择所属企业")
        ent = db.get(Enterprise, body.enterprise_id)
        if ent is None:
            raise HTTPException(status_code=404, detail="企业不存在")
        eid = body.enterprise_id
    else:
        if current.enterprise_id is None:
            raise HTTPException(status_code=400, detail="当前账号未关联企业")
        if body.enterprise_id is not None:
            ensure_in_managed_enterprise_scope(db, current, body.enterprise_id)
            eid = body.enterprise_id
        else:
            eid = current.enterprise_id
    dup = db.scalar(
        select(func.count())
        .select_from(PaperLevel)
        .where(
            PaperLevel.enterprise_id == eid,
            PaperLevel.level_code == body.level_code.strip(),
        )
    )
    if dup:
        raise HTTPException(status_code=400, detail="该企业下等级编号已存在")
    row = PaperLevel(
        level_code=body.level_code.strip(),
        level_name=body.level_name.strip(),
        title_series=body.title_series.strip(),
        enterprise_id=eid,
        created_by=current.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    row = db.scalars(
        select(PaperLevel).options(joinedload(PaperLevel.enterprise)).where(PaperLevel.id == row.id)
    ).first()
    assert row is not None
    return _out_from_row(db, row)


@router.get("/{level_id}", response_model=PaperLevelOut)
def get_paper_level(
    level_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.paper_level"))],
) -> PaperLevelOut:
    row = db.scalars(
        select(PaperLevel).options(joinedload(PaperLevel.enterprise)).where(PaperLevel.id == level_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="试卷等级不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, row.enterprise_id)
    return _out_from_row(db, row)


@router.patch("/{level_id}", response_model=PaperLevelOut)
def update_paper_level(
    level_id: int,
    body: PaperLevelUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper_level.manage"))],
) -> PaperLevelOut:
    row = db.get(PaperLevel, level_id)
    if row is None:
        raise HTTPException(status_code=404, detail="试卷等级不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, row.enterprise_id)
    if body.level_code is not None:
        code = body.level_code.strip()
        dup = db.scalar(
            select(func.count())
            .select_from(PaperLevel)
            .where(
                PaperLevel.enterprise_id == row.enterprise_id,
                PaperLevel.level_code == code,
                PaperLevel.id != level_id,
            )
        )
        if dup:
            raise HTTPException(status_code=400, detail="该企业下等级编号已存在")
        row.level_code = code
    if body.level_name is not None:
        row.level_name = body.level_name.strip()
    if body.title_series is not None:
        row.title_series = body.title_series.strip()
    db.commit()
    db.refresh(row)
    row = db.scalars(
        select(PaperLevel).options(joinedload(PaperLevel.enterprise)).where(PaperLevel.id == level_id)
    ).first()
    assert row is not None
    return _out_from_row(db, row)


@router.delete("/{level_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paper_level(
    level_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper_level.manage"))],
) -> None:
    row = db.get(PaperLevel, level_id)
    if row is None:
        raise HTTPException(status_code=404, detail="试卷等级不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, row.enterprise_id)
    db.delete(row)
    db.commit()
