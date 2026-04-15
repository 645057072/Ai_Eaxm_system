# -*- coding: utf-8 -*-
"""考试服务记录列表（交卷自动生成）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, false, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.core.permissions import is_super_role
from app.models.exam_service_record import ExamServiceRecord
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.exam_service_record import ExamServiceRecordOut
from app.services.data_scope import get_managed_enterprise_ids

router = APIRouter()


def _restrict_by_enterprise(q, cnt_q, db: Session, current: User):
    if is_super_role(current):
        return q, cnt_q
    managed = get_managed_enterprise_ids(db, current)
    if not managed:
        return q.where(false()), cnt_q.where(false())
    return q.where(ExamServiceRecord.enterprise_id.in_(managed)), cnt_q.where(
        ExamServiceRecord.enterprise_id.in_(managed)
    )


@router.get("", response_model=PageResult[ExamServiceRecordOut])
def list_exam_service_records(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.exam_service_record"))],
    page: Annotated[PageParams, Depends()],
    keyword: str | None = Query(default=None, description="考试编号/课程/试卷/企业/学员模糊"),
) -> PageResult[ExamServiceRecordOut]:
    """分页列表。"""
    conds: list = []
    kw = (keyword or "").strip()
    if kw:
        like = f"%{kw}%"
        conds.append(
            or_(
                ExamServiceRecord.exam_no.like(like),
                ExamServiceRecord.course_name.like(like),
                ExamServiceRecord.paper_title.like(like),
                ExamServiceRecord.enterprise_name.like(like),
                ExamServiceRecord.student_display.like(like),
            )
        )
    w = and_(*conds) if conds else None

    base = select(ExamServiceRecord)
    cnt = select(func.count()).select_from(ExamServiceRecord)
    base, cnt = _restrict_by_enterprise(base, cnt, db, current)
    if w is not None:
        base = base.where(w)
        cnt = cnt.where(w)
    total = db.scalar(cnt) or 0
    rows = db.scalars(
        base.order_by(ExamServiceRecord.id.desc()).offset(page.skip).limit(page.limit)
    ).all()
    items = [ExamServiceRecordOut.model_validate(r) for r in rows]
    return PageResult[ExamServiceRecordOut](total=int(total), items=items)
