# -*- coding: utf-8 -*-
"""按所属企业、所属课程、题型生成唯一题号。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.question import Question

_QTYPE_ABBR = {"judge": "J", "single": "S", "multiple": "M", "fill": "F"}


def allocate_question_no(
    db: Session,
    enterprise_id: int | None,
    course_id: int | None,
    q_type: str,
) -> str:
    """格式：{企业id}-{课程id}-{题型简码}-{序号4位}，如 1-6-S-0001。未选企业/课程时用 0 占位。"""
    eid = enterprise_id if enterprise_id is not None else 0
    cid = course_id if course_id is not None else 0
    abbr = _QTYPE_ABBR.get(q_type, "X")
    prefix = f"{eid}-{cid}-{abbr}-"
    rows = db.scalars(select(Question.question_no).where(Question.question_no.like(f"{prefix}%"))).all()
    mx = 0
    for qn in rows:
        if not qn or not isinstance(qn, str):
            continue
        if not qn.startswith(prefix):
            continue
        suf = qn[len(prefix) :]
        if suf.isdigit():
            mx = max(mx, int(suf))
    return f"{prefix}{mx + 1:04d}"
