# -*- coding: utf-8 -*-
"""考试场次：发布、考生可见数据、开始作答。"""

import secrets
import string
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, false, func, or_, select
from sqlalchemy.orm import Session, aliased, joinedload

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.permissions import is_super_role
from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.exam import ExamAttempt, ExamPaper, ExamPaperItem, ExamSession
from app.models.user import User
from app.schemas.attempt import AttemptStartOut
from app.schemas.common import PageParams, PageResult
from app.schemas.exam_take import TakeDataOut, TakeQuestionItem
from app.schemas.session import ExamSessionCreate, ExamSessionOut, ExamSessionUpdate
from app.services.data_scope import (
    assert_paper_in_enterprise,
    assert_session_in_enterprise,
    ensure_in_managed_enterprise_scope,
    get_managed_enterprise_ids,
    session_list_tenant_filter,
)

router = APIRouter()


def _session_out_load_options():
    """列表/详情返回 ExamSessionOut 时统一预加载。"""
    return (
        joinedload(ExamSession.enterprise),
        joinedload(ExamSession.course),
        joinedload(ExamSession.paper),
        joinedload(ExamSession.creator),
        joinedload(ExamSession.publisher),
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dt_as_utc(dt: datetime) -> datetime:
    """与数据库存储混用 naive/aware 时统一为 UTC，避免比较报错500。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _user_display_name(u: User | None) -> str | None:
    if u is None:
        return None
    if u.full_name and str(u.full_name).strip():
        return str(u.full_name).strip()
    return u.username or None


def _allocate_session_code(db: Session) -> str:
    """生成全系统唯一的场次编码（大写字母与数字）。"""
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(64):
        suffix = "".join(secrets.choice(alphabet) for _ in range(8))
        code = f"SES{suffix}"
        if not db.scalar(
            select(func.count()).select_from(ExamSession).where(ExamSession.session_code == code)
        ):
            return code
    raise HTTPException(status_code=500, detail="无法生成场次编码")


def _validate_session_business(
    db: Session,
    current: User,
    *,
    paper_id: int,
    enterprise_id: int,
    course_id: int,
) -> None:
    """场次所属企业、课程与试卷一致且在数据权限内。"""
    ensure_in_managed_enterprise_scope(db, current, enterprise_id)
    paper = db.get(ExamPaper, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    assert_paper_in_enterprise(db, current, paper_id)
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if course.enterprise_id != enterprise_id:
        raise HTTPException(status_code=400, detail="课程与所属企业不一致")
    if paper.course_id is not None and paper.course_id != course_id:
        raise HTTPException(status_code=400, detail="所选课程与试卷已关联课程不一致")


def _resolve_attempt_limit_for_paper(paper: ExamPaper, raw: int | None) -> int | None:
    """练习卷不限制；模拟/正式默认 1 次，可手工调大。"""
    if paper.paper_type == "practice":
        return None
    if raw is None:
        return 1
    if raw < 1:
        raise HTTPException(status_code=400, detail="次数限制至少为 1")
    return raw


def _session_to_out(s: ExamSession) -> ExamSessionOut:
    paper_no = s.paper.paper_no if s.paper is not None else None
    paper_title = s.paper.title if s.paper is not None else None
    paper_type = s.paper.paper_type if s.paper is not None else None
    paper_duration = s.paper.duration_minutes if s.paper is not None else None
    return ExamSessionOut(
        id=s.id,
        session_code=s.session_code,
        enterprise_id=s.enterprise_id,
        course_id=s.course_id,
        enterprise_name=s.enterprise.name if s.enterprise else None,
        course_name=s.course.name if s.course else None,
        paper_id=s.paper_id,
        paper_no=paper_no,
        paper_title=paper_title,
        paper_type=paper_type,
        paper_duration_minutes=paper_duration,
        attempt_limit=s.attempt_limit,
        title=s.title,
        start_at=s.start_at,
        end_at=s.end_at,
        status=s.status,
        created_by=s.created_by,
        operator_name=_user_display_name(s.creator),
        published_by=s.published_by,
        publisher_name=_user_display_name(s.publisher),
        created_at=s.created_at,
        updated_at=s.updated_at,
        paper=None,
    )


def _assert_publish_within_exam_window(s: ExamSession) -> None:
    """场次发布仅在考试开放时间内允许（开始前、结束后均不可发布）。"""
    if s.start_at is None or s.end_at is None:
        raise HTTPException(status_code=400, detail="请先设置考试开始与结束时间后再发布")
    now = _now()
    start = _dt_as_utc(s.start_at)
    end = _dt_as_utc(s.end_at)
    if not (start <= now <= end):
        raise HTTPException(status_code=400, detail="仅在考试开放时间内允许发布场次")


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
    paper_title_keyword: str | None = Query(default=None, description="试卷标题模糊查询"),
    course_keyword: str | None = Query(default=None, description="课程名称模糊查询"),
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
    # 考生端仅展示本人所属企业的场次（场次表 enterprise_id，与企业管理一致）
    if not is_super_role(current):
        if current.enterprise_id is None:
            return PageResult[ExamSessionOut](total=0, items=[])
        conds.append(ExamSession.enterprise_id == current.enterprise_id)

    SessionCourse = aliased(Course)

    def _apply_available_filters(q):
        q = q.where(*conds)
        pt = (paper_title_keyword or "").strip()
        if pt:
            q = q.where(ExamPaper.title.ilike(f"%{pt}%"))
        ck = (course_keyword or "").strip()
        if ck:
            q = q.join(SessionCourse, ExamSession.course_id == SessionCourse.id).where(
                SessionCourse.name.ilike(f"%{ck}%")
            )
        return q

    cnt_base = select(func.count()).select_from(ExamSession).join(ExamPaper, ExamSession.paper_id == ExamPaper.id)
    total = db.scalar(_apply_available_filters(cnt_base)) or 0
    data_q = select(ExamSession).join(ExamPaper, ExamSession.paper_id == ExamPaper.id)
    rows = db.scalars(
        _apply_available_filters(data_q)
        .options(*_session_out_load_options())
        .order_by(ExamSession.id.desc())
        .offset(page.skip)
        .limit(page.limit)
    ).all()
    return PageResult[ExamSessionOut](total=int(total), items=[_session_to_out(r) for r in rows])


@router.get("", response_model=PageResult[ExamSessionOut])
def list_sessions(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User, Depends(require_any_permission("list.session", "menu.exam.paper_publish"))
    ],
    page: Annotated[PageParams, Depends()],
    status: str | None = None,
    enterprise_id: int | None = Query(default=None, ge=1, description="按所属企业筛选"),
    course_id: int | None = Query(default=None, ge=1, description="按关联课程筛选"),
    title_keyword: str | None = Query(
        default=None, description="场次标题或试卷名称模糊查询",
    ),
    enterprise_keyword: str | None = Query(
        default=None, description="所属企业名称模糊查询（非超管限定在当前用户可管理企业范围内）"
    ),
    course_keyword: str | None = Query(
        default=None, description="课程名称模糊查询（非超管限定在当前用户可管理企业下的课程）"
    ),
) -> PageResult[ExamSessionOut]:
    """本企业场次列表。"""
    PaperCreator = aliased(User)
    PaperCourse = aliased(Course)
    SessionCourse = aliased(Course)
    stmt = (
        select(func.count())
        .select_from(ExamSession)
        .join(ExamPaper, ExamSession.paper_id == ExamPaper.id)
        .outerjoin(PaperCourse, ExamPaper.course_id == PaperCourse.id)
        .outerjoin(PaperCreator, ExamPaper.created_by == PaperCreator.id)
    )
    if not is_super_role(current):
        tf = session_list_tenant_filter(PaperCreator, db, current, scope_course=PaperCourse)
        stmt = stmt.where(tf)
    if status:
        stmt = stmt.where(ExamSession.status == status)
    if enterprise_id is not None:
        if not is_super_role(current):
            ensure_in_managed_enterprise_scope(db, current, enterprise_id)
        stmt = stmt.where(ExamSession.enterprise_id == enterprise_id)
    if course_id is not None:
        stmt = stmt.where(ExamSession.course_id == course_id)
    if title_keyword and title_keyword.strip():
        kw = f"%{title_keyword.strip()}%"
        stmt = stmt.where(or_(ExamSession.title.ilike(kw), ExamPaper.title.ilike(kw)))
    if enterprise_keyword and enterprise_keyword.strip():
        kw = f"%{enterprise_keyword.strip()}%"
        stmt = stmt.join(Enterprise, ExamSession.enterprise_id == Enterprise.id)
        if not is_super_role(current):
            managed = get_managed_enterprise_ids(db, current)
            if not managed:
                stmt = stmt.where(false())
            else:
                stmt = stmt.where(and_(Enterprise.name.ilike(kw), Enterprise.id.in_(managed)))
        else:
            stmt = stmt.where(Enterprise.name.ilike(kw))
    if course_keyword and course_keyword.strip():
        kw = f"%{course_keyword.strip()}%"
        stmt = stmt.join(SessionCourse, ExamSession.course_id == SessionCourse.id)
        if not is_super_role(current):
            managed = get_managed_enterprise_ids(db, current)
            if not managed:
                stmt = stmt.where(false())
            else:
                stmt = stmt.where(
                    and_(SessionCourse.name.ilike(kw), SessionCourse.enterprise_id.in_(managed))
                )
        else:
            stmt = stmt.where(SessionCourse.name.ilike(kw))
    total = db.scalar(stmt) or 0
    q = (
        select(ExamSession)
        .join(ExamPaper, ExamSession.paper_id == ExamPaper.id)
        .outerjoin(PaperCourse, ExamPaper.course_id == PaperCourse.id)
        .outerjoin(PaperCreator, ExamPaper.created_by == PaperCreator.id)
    )
    if not is_super_role(current):
        q = q.where(session_list_tenant_filter(PaperCreator, db, current, scope_course=PaperCourse))
    if status:
        q = q.where(ExamSession.status == status)
    if enterprise_id is not None:
        q = q.where(ExamSession.enterprise_id == enterprise_id)
    if course_id is not None:
        q = q.where(ExamSession.course_id == course_id)
    if title_keyword and title_keyword.strip():
        kw = f"%{title_keyword.strip()}%"
        q = q.where(or_(ExamSession.title.ilike(kw), ExamPaper.title.ilike(kw)))
    if enterprise_keyword and enterprise_keyword.strip():
        kw = f"%{enterprise_keyword.strip()}%"
        q = q.join(Enterprise, ExamSession.enterprise_id == Enterprise.id)
        if not is_super_role(current):
            managed = get_managed_enterprise_ids(db, current)
            if not managed:
                q = q.where(false())
            else:
                q = q.where(and_(Enterprise.name.ilike(kw), Enterprise.id.in_(managed)))
        else:
            q = q.where(Enterprise.name.ilike(kw))
    if course_keyword and course_keyword.strip():
        kw = f"%{course_keyword.strip()}%"
        q = q.join(SessionCourse, ExamSession.course_id == SessionCourse.id)
        if not is_super_role(current):
            managed = get_managed_enterprise_ids(db, current)
            if not managed:
                q = q.where(false())
            else:
                q = q.where(
                    and_(SessionCourse.name.ilike(kw), SessionCourse.enterprise_id.in_(managed))
                )
        else:
            q = q.where(SessionCourse.name.ilike(kw))
    rows = db.scalars(
        q.options(*_session_out_load_options())
        .offset(page.skip)
        .limit(page.limit)
        .order_by(ExamSession.id.desc())
    ).all()
    return PageResult[ExamSessionOut](total=int(total), items=[_session_to_out(r) for r in rows])


@router.post("", response_model=ExamSessionOut)
def create_session(
    body: ExamSessionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User, Depends(require_any_permission("action.session.manage", "menu.exam.paper_publish"))
    ],
) -> ExamSessionOut:
    """创建场次。"""
    if body.session_code:
        code = body.session_code
        if db.scalar(select(func.count()).select_from(ExamSession).where(ExamSession.session_code == code)):
            raise HTTPException(status_code=400, detail="场次编码已存在")
    else:
        code = _allocate_session_code(db)
    _validate_session_business(
        db,
        current,
        paper_id=body.paper_id,
        enterprise_id=body.enterprise_id,
        course_id=body.course_id,
    )
    _assert_paper_valid_for_session(db, body.paper_id)
    paper = db.get(ExamPaper, body.paper_id)
    assert paper is not None
    lim = _resolve_attempt_limit_for_paper(paper, body.attempt_limit)
    s = ExamSession(
        session_code=code,
        enterprise_id=body.enterprise_id,
        course_id=body.course_id,
        paper_id=body.paper_id,
        title=body.title,
        start_at=body.start_at,
        end_at=body.end_at,
        status="draft",
        created_by=current.id,
        attempt_limit=lim,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    s2 = db.scalars(
        select(ExamSession).options(*_session_out_load_options()).where(ExamSession.id == s.id)
    ).first()
    assert s2 is not None
    return _session_to_out(s2)


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
                "menu.exam.paper_publish",
                "menu.exam.available",
                "action.exam.take",
            )
        ),
    ],
) -> ExamSessionOut:
    """场次详情。"""
    s = db.scalars(
        select(ExamSession).options(*_session_out_load_options()).where(ExamSession.id == session_id)
    ).first()
    if s is None:
        raise HTTPException(status_code=404, detail="场次不存在")
    assert_session_in_enterprise(db, current, session_id)
    return _session_to_out(s)


@router.patch("/{session_id}", response_model=ExamSessionOut)
def update_session(
    session_id: int,
    body: ExamSessionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User, Depends(require_any_permission("action.session.manage", "menu.exam.paper_publish"))
    ],
) -> ExamSessionOut:
    s = assert_session_in_enterprise(db, current, session_id)
    if s.status != "draft":
        raise HTTPException(status_code=400, detail="仅草稿场次可修改")
    data = body.model_dump(exclude_unset=True)
    attempt_in = "attempt_limit" in data
    attempt_patch = data.pop("attempt_limit", None) if attempt_in else None
    if "session_code" in data and data["session_code"] is not None:
        sc = data["session_code"].strip()
        if sc != s.session_code and (
            db.scalar(
                select(func.count()).select_from(ExamSession).where(
                    ExamSession.session_code == sc, ExamSession.id != session_id
                )
            )
        ):
            raise HTTPException(status_code=400, detail="场次编码已存在")
        data["session_code"] = sc
    pid = data.get("paper_id", s.paper_id)
    eid = data.get("enterprise_id", s.enterprise_id)
    cid = data.get("course_id", s.course_id)
    if any(k in data for k in ("paper_id", "enterprise_id", "course_id")):
        if cid is None:
            raise HTTPException(status_code=400, detail="请指定关联课程")
        _validate_session_business(db, current, paper_id=pid, enterprise_id=eid, course_id=cid)
    for k, v in data.items():
        setattr(s, k, v)
    paper = db.get(ExamPaper, s.paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    if attempt_in or "paper_id" in data:
        raw_lim = attempt_patch if attempt_in else s.attempt_limit
        s.attempt_limit = _resolve_attempt_limit_for_paper(paper, raw_lim)
    db.commit()
    db.refresh(s)
    s2 = db.scalars(
        select(ExamSession).options(*_session_out_load_options()).where(ExamSession.id == session_id)
    ).first()
    assert s2 is not None
    return _session_to_out(s2)


@router.post("/{session_id}/publish", response_model=ExamSessionOut)
def publish_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User, Depends(require_any_permission("action.session.manage", "menu.exam.paper_publish"))
    ],
) -> ExamSessionOut:
    """发布场次。"""
    s = assert_session_in_enterprise(db, current, session_id)
    if s.status == "published":
        raise HTTPException(status_code=400, detail="场次已发布")
    _assert_paper_valid_for_session(db, s.paper_id)
    _assert_publish_within_exam_window(s)
    s.status = "published"
    s.published_by = current.id
    db.commit()
    db.refresh(s)
    s2 = db.scalars(
        select(ExamSession).options(*_session_out_load_options()).where(ExamSession.id == session_id)
    ).first()
    assert s2 is not None
    return _session_to_out(s2)


def _assert_unpublish_not_blocked_by_attempts(db: Session, session_id: int, s: ExamSession) -> None:
    """已发布场次若已有考生作答（试卷发布侧已形成关联），禁止反发布。"""
    if s.status != "published":
        return
    n = (
        db.scalar(
            select(func.count()).select_from(ExamAttempt).where(ExamAttempt.session_id == session_id)
        )
        or 0
    )
    if int(n) > 0:
        raise HTTPException(
            status_code=400,
            detail="该场次已发布且存在考生作答记录，与试卷发布业务已关联，禁止反发布",
        )


@router.post("/{session_id}/unpublish", response_model=ExamSessionOut)
def unpublish_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User, Depends(require_any_permission("action.session.manage", "menu.exam.paper_publish"))
    ],
) -> ExamSessionOut:
    """反发布：场次改回草稿，考生端不可见。"""
    s = assert_session_in_enterprise(db, current, session_id)
    _assert_unpublish_not_blocked_by_attempts(db, session_id, s)
    s.status = "draft"
    s.published_by = None
    db.commit()
    db.refresh(s)
    s2 = db.scalars(
        select(ExamSession).options(*_session_out_load_options()).where(ExamSession.id == session_id)
    ).first()
    assert s2 is not None
    return _session_to_out(s2)


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User, Depends(require_any_permission("action.session.manage", "menu.exam.paper_publish"))
    ],
) -> None:
    """删除场次（级联删除作答记录）。"""
    s = assert_session_in_enterprise(db, current, session_id)
    if s.status != "draft":
        raise HTTPException(status_code=400, detail="仅草稿场次可删除")
    db.delete(s)
    db.commit()


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
    if s.start_at is None or s.end_at is None:
        raise HTTPException(status_code=400, detail="考试时间未设置，无法进入考试")
    sa = _dt_as_utc(s.start_at)
    ea = _dt_as_utc(s.end_at)
    if now < sa:
        raise HTTPException(status_code=400, detail="考试尚未开始，无法进入考试")
    if now > ea:
        raise HTTPException(status_code=400, detail="考试已结束，无法进入考试")
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
        paper_type=paper.paper_type or "formal",
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
    if s.start_at is None or s.end_at is None:
        raise HTTPException(status_code=400, detail="考试时间未设置，无法进入考试")
    sa = _dt_as_utc(s.start_at)
    ea = _dt_as_utc(s.end_at)
    if now < sa:
        raise HTTPException(status_code=400, detail="考试尚未开始，无法进入考试")
    if now > ea:
        raise HTTPException(status_code=400, detail="考试已结束，无法进入考试")
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
        ptype = (
            (existing.session.paper.paper_type or "formal")
            if existing.session and existing.session.paper
            else "formal"
        )
        return AttemptStartOut(
            attempt_id=existing.id,
            session_id=s.id,
            paper_id=s.paper_id,
            duration_minutes=dur,
            started_at=existing.started_at,
            status=existing.status,
            paper_type=ptype,
            staged=bool(getattr(existing, "staged", False)),
        )
    lim = s.attempt_limit
    if lim is not None and lim >= 1:
        cnt = (
            db.scalar(
                select(func.count()).select_from(ExamAttempt).where(
                    ExamAttempt.session_id == session_id,
                    ExamAttempt.user_id == current.id,
                )
            )
            or 0
        )
        if int(cnt) >= lim:
            raise HTTPException(status_code=400, detail="已达本场考试答题次数上限")
    att = ExamAttempt(session_id=session_id, user_id=current.id, status="in_progress")
    db.add(att)
    db.commit()
    db.refresh(att)
    dur = s.paper.duration_minutes if s.paper else 60
    ptype = (s.paper.paper_type or "formal") if s.paper else "formal"
    return AttemptStartOut(
        attempt_id=att.id,
        session_id=s.id,
        paper_id=s.paper_id,
        duration_minutes=dur,
        started_at=att.started_at,
        status=att.status,
        paper_type=ptype,
        staged=False,
    )
