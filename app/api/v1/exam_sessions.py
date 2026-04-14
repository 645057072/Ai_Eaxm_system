# -*- coding: utf-8 -*-
"""考试场次：发布、考生可见数据、开始作答。"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, aliased, joinedload

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.permissions import is_super_role
from app.models.course import Course
from app.models.exam import ExamAttempt, ExamPaper, ExamPaperItem, ExamSession
from app.models.user import User
from app.schemas.attempt import AttemptStartOut
from app.schemas.common import PageParams, PageResult
from app.schemas.exam_take import TakeDataOut, TakeQuestionItem
from app.schemas.session import ExamSessionCreate, ExamSessionOut, ExamSessionUpdate
from app.services.data_scope import assert_paper_in_enterprise, assert_session_in_enterprise

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _assert_paper_valid_for_session(db: Session, paper_id: int) -> None:
    """试卷未设置有效期或当前日期未超过有效期截止日，才允许创建/发布场次。"""
    paper = db.get(ExamPaper, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    vu = getattr(paper, "valid_until", None)
    if vu is None:
        return
    today = _now().date()
    if hasattr(vu, "date"):
        vu_d = vu.date()
    else:
        vu_d = vu
    if today > vu_d:
        raise HTTPException(status_code=400, detail="试卷已超过有效期，无法创建或发布考试场次")


@router.get("/available/list", response_model=PageResult[ExamSessionOut])
def list_available_for_student(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("menu.exam.available"))],
    page: Annotated[PageParams, Depends()],
) -> PageResult[ExamSessionOut]:
    """考生可见的本企业场次。"""
    now = _now()
    conds = [
        ExamSession.status == "published",
        ExamSession.start_at.is_not(None),
        ExamSession.end_at.is_not(None),
        ExamSession.start_at <= now,
        ExamSession.end_at >= now,
    ]
    PaperCreator = aliased(User)
    if not is_super_role(current):
        if current.enterprise_id is None:
            return PageResult[ExamSessionOut](total=0, items=[])
        tenant_or = or_(
            Course.enterprise_id == current.enterprise_id,
            and_(ExamPaper.course_id.is_(None), PaperCreator.enterprise_id == current.enterprise_id),
        )
        conds.append(tenant_or)
    total = (
        db.scalar(
            select(func.count())
            .select_from(ExamSession)
            .join(ExamPaper, ExamSession.paper_id == ExamPaper.id)
            .outerjoin(Course, ExamPaper.course_id == Course.id)
            .outerjoin(PaperCreator, ExamPaper.created_by == PaperCreator.id)
            .where(*conds)
        )
        or 0
    )
    rows = db.scalars(
        select(ExamSession)
        .join(ExamPaper, ExamSession.paper_id == ExamPaper.id)
        .outerjoin(Course, ExamPaper.course_id == Course.id)
        .outerjoin(PaperCreator, ExamPaper.created_by == PaperCreator.id)
        .where(*conds)
        .order_by(ExamSession.id.desc())
        .offset(page.skip)
        .limit(page.limit)
    ).all()
    return PageResult[ExamSessionOut](total=int(total), items=[ExamSessionOut.model_validate(r) for r in rows])


@router.get("", response_model=PageResult[ExamSessionOut])
def list_sessions(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.session"))],
    page: Annotated[PageParams, Depends()],
    status: str | None = None,
) -> PageResult[ExamSessionOut]:
    """本企业场次列表。"""
    PaperCreator = aliased(User)
    stmt = (
        select(func.count())
        .select_from(ExamSession)
        .join(ExamPaper, ExamSession.paper_id == ExamPaper.id)
        .outerjoin(Course, ExamPaper.course_id == Course.id)
        .outerjoin(PaperCreator, ExamPaper.created_by == PaperCreator.id)
    )
    if not is_super_role(current):
        if current.enterprise_id is None:
            return PageResult[ExamSessionOut](total=0, items=[])
        stmt = stmt.where(
            or_(
                Course.enterprise_id == current.enterprise_id,
                and_(ExamPaper.course_id.is_(None), PaperCreator.enterprise_id == current.enterprise_id),
            )
        )
    if status:
        stmt = stmt.where(ExamSession.status == status)
    total = db.scalar(stmt) or 0
    q = (
        select(ExamSession)
        .join(ExamPaper, ExamSession.paper_id == ExamPaper.id)
        .outerjoin(Course, ExamPaper.course_id == Course.id)
        .outerjoin(PaperCreator, ExamPaper.created_by == PaperCreator.id)
    )
    if not is_super_role(current):
        q = q.where(
            or_(
                Course.enterprise_id == current.enterprise_id,
                and_(ExamPaper.course_id.is_(None), PaperCreator.enterprise_id == current.enterprise_id),
            )
        )
    if status:
        q = q.where(ExamSession.status == status)
    rows = db.scalars(q.offset(page.skip).limit(page.limit).order_by(ExamSession.id.desc())).all()
    return PageResult[ExamSessionOut](total=int(total), items=[ExamSessionOut.model_validate(r) for r in rows])


@router.post("", response_model=ExamSessionOut)
def create_session(
    body: ExamSessionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.session.manage"))],
) -> ExamSessionOut:
    """创建场次。"""
    assert_paper_in_enterprise(db, current, body.paper_id)
    _assert_paper_valid_for_session(db, body.paper_id)
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
    current: Annotated[
        User,
        Depends(
            require_any_permission(
                "list.session",
                "action.session.manage",
                "menu.exam.available",
                "action.exam.take",
            )
        ),
    ],
) -> ExamSessionOut:
    """场次详情。"""
    s = db.get(ExamSession, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="场次不存在")
    assert_session_in_enterprise(db, current, session_id)
    return ExamSessionOut.model_validate(s)


@router.patch("/{session_id}", response_model=ExamSessionOut)
def update_session(
    session_id: int,
    body: ExamSessionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.session.manage"))],
) -> ExamSessionOut:
    s = assert_session_in_enterprise(db, current, session_id)
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
    current: Annotated[User, Depends(require_permission("action.session.manage"))],
) -> ExamSessionOut:
    """发布场次。"""
    s = assert_session_in_enterprise(db, current, session_id)
    _assert_paper_valid_for_session(db, s.paper_id)
    s.status = "published"
    db.commit()
    db.refresh(s)
    return ExamSessionOut.model_validate(s)


@router.get("/{session_id}/take-data", response_model=TakeDataOut)
def get_take_data(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.exam.take"))],
) -> TakeDataOut:
    """获取本场考试题目（不含标准答案）。"""
    assert_session_in_enterprise(db, current, session_id)
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
    current: Annotated[User, Depends(require_permission("action.exam.take"))],
) -> AttemptStartOut:
    """开始考试，生成唯一作答记录。"""
    assert_session_in_enterprise(db, current, session_id)
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
