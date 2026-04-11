# -*- coding: utf-8 -*-
"""考试场次：发布、考生可见数据、开始作答。"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_roles
from app.models.exam import ExamAttempt, ExamPaper, ExamPaperItem, ExamSession
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.exam_take import TakeDataOut, TakeQuestionItem
from app.schemas.session import ExamSessionCreate, ExamSessionOut, ExamSessionUpdate
from app.schemas.attempt import AttemptStartOut

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/available/list", response_model=PageResult[ExamSessionOut])
def list_available_for_student(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("student"))],
    page: Annotated[PageParams, Depends()],
) -> PageResult[ExamSessionOut]:
    """考生可见：已发布且当前时间在开始与结束之间的场次（须放在 /{session_id} 之前）。"""
    now = _now()
    conds = [
        ExamSession.status == "published",
        ExamSession.start_at.is_not(None),
        ExamSession.end_at.is_not(None),
        ExamSession.start_at <= now,
        ExamSession.end_at >= now,
    ]
    total = db.scalar(select(func.count()).select_from(ExamSession).where(*conds)) or 0
    rows = db.scalars(
        select(ExamSession)
        .where(*conds)
        .order_by(ExamSession.id.desc())
        .offset(page.skip)
        .limit(page.limit)
    ).all()
    return PageResult[ExamSessionOut](total=int(total), items=[ExamSessionOut.model_validate(r) for r in rows])


@router.get("", response_model=PageResult[ExamSessionOut])
def list_sessions(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
    page: Annotated[PageParams, Depends()],
    status: str | None = None,
) -> PageResult[ExamSessionOut]:
    """场次列表（教师/管理员）。"""
    stmt = select(func.count()).select_from(ExamSession)
    if status:
        stmt = stmt.where(ExamSession.status == status)
    total = db.scalar(stmt) or 0
    q = select(ExamSession)
    if status:
        q = q.where(ExamSession.status == status)
    rows = db.scalars(q.offset(page.skip).limit(page.limit).order_by(ExamSession.id.desc())).all()
    return PageResult[ExamSessionOut](total=int(total), items=[ExamSessionOut.model_validate(r) for r in rows])


@router.post("", response_model=ExamSessionOut)
def create_session(
    body: ExamSessionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> ExamSessionOut:
    """创建场次。"""
    if db.get(ExamPaper, body.paper_id) is None:
        raise HTTPException(status_code=400, detail="试卷不存在")
    s = ExamSession(
        paper_id=body.paper_id,
        title=body.title,
        start_at=body.start_at,
        end_at=body.end_at,
        status="draft",
        created_by=current.id,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return ExamSessionOut.model_validate(s)


@router.get("/{session_id}", response_model=ExamSessionOut)
def get_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher", "student"))],
) -> ExamSessionOut:
    """场次详情。"""
    s = db.get(ExamSession, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="场次不存在")
    return ExamSessionOut.model_validate(s)


@router.patch("/{session_id}", response_model=ExamSessionOut)
def update_session(
    session_id: int,
    body: ExamSessionUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> ExamSessionOut:
    s = db.get(ExamSession, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="场次不存在")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return ExamSessionOut.model_validate(s)


@router.post("/{session_id}/publish", response_model=ExamSessionOut)
def publish_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> ExamSessionOut:
    """发布场次。"""
    s = db.get(ExamSession, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="场次不存在")
    s.status = "published"
    db.commit()
    db.refresh(s)
    return ExamSessionOut.model_validate(s)


@router.get("/{session_id}/take-data", response_model=TakeDataOut)
def get_take_data(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("student"))],
) -> TakeDataOut:
    """获取本场考试题目（不含标准答案）。"""
    s = db.scalars(
        select(ExamSession)
        .options(joinedload(ExamSession.paper).joinedload(ExamPaper.items).joinedload(ExamPaperItem.question))
        .where(ExamSession.id == session_id)
    ).first()
    if s is None:
        raise HTTPException(status_code=404, detail="场次不存在")
    now = _now()
    if s.status != "published":
        raise HTTPException(status_code=400, detail="考试未发布")
    if s.start_at is None or s.end_at is None or not (s.start_at <= now <= s.end_at):
        raise HTTPException(status_code=400, detail="不在考试时间范围内")
    paper = s.paper
    if paper is None:
        raise HTTPException(status_code=400, detail="试卷缺失")
    items: list[TakeQuestionItem] = []
    for it in sorted(paper.items, key=lambda x: (x.sort_order, x.id)):
        q = it.question
        if q is None:
            continue
        items.append(
            TakeQuestionItem(
                question_id=q.id,
                q_type=q.q_type,
                stem=q.stem,
                options_json=q.options_json,
                score=it.score,
            )
        )
    return TakeDataOut(
        session_id=s.id,
        title=s.title,
        paper_id=paper.id,
        duration_minutes=paper.duration_minutes,
        questions=items,
    )


@router.post("/{session_id}/start", response_model=AttemptStartOut)
def start_attempt(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_roles("student"))],
) -> AttemptStartOut:
    """开始考试，生成唯一作答记录。"""
    s = db.scalars(
        select(ExamSession).options(joinedload(ExamSession.paper)).where(ExamSession.id == session_id)
    ).first()
    if s is None:
        raise HTTPException(status_code=404, detail="场次不存在")
    now = _now()
    if s.status != "published":
        raise HTTPException(status_code=400, detail="考试未发布")
    if s.start_at is None or s.end_at is None or not (s.start_at <= now <= s.end_at):
        raise HTTPException(status_code=400, detail="不在考试时间范围内")
    existing = db.scalars(
        select(ExamAttempt)
        .options(joinedload(ExamAttempt.session).joinedload(ExamSession.paper))
        .where(
            ExamAttempt.session_id == session_id,
            ExamAttempt.user_id == current.id,
        )
    ).first()
    if existing:
        dur = existing.session.paper.duration_minutes if existing.session and existing.session.paper else 60
        return AttemptStartOut(
            attempt_id=existing.id,
            session_id=s.id,
            paper_id=s.paper_id,
            duration_minutes=dur,
            started_at=existing.started_at,
            status=existing.status,
        )
    att = ExamAttempt(session_id=session_id, user_id=current.id, status="in_progress")
    db.add(att)
    db.commit()
    db.refresh(att)
    dur = s.paper.duration_minutes if s.paper else 60
    return AttemptStartOut(
        attempt_id=att.id,
        session_id=s.id,
        paper_id=s.paper_id,
        duration_minutes=dur,
        started_at=att.started_at,
        status=att.status,
    )
