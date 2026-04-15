# -*- coding: utf-8 -*-
"""试卷：组卷与题目项维护。"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session, aliased, joinedload

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.permissions import is_super_role
from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.exam import ExamPaper, ExamPaperItem, ExamSession
from app.models.paper_level import PaperLevel
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.paper import (
    PaperBatchCreate,
    PaperBatchIdsIn,
    PaperBatchOut,
    PaperCreate,
    PaperItemAdd,
    PaperItemOut,
    PaperOut,
    PaperSummary,
    PaperUpdate,
)
from app.schemas.question import QuestionOut
from app.services.data_scope import (
    assert_paper_in_enterprise,
    assert_question_in_enterprise,
    ensure_in_managed_enterprise_scope,
    restrict_exam_paper_query_by_tenant,
)
from app.services.paper_batch import build_disjoint_chunks_for_type, merge_items_in_rule_order
from app.services.paper_compose import fetch_question_pool_ids, pick_questions_for_rule, rules_to_jsonable

router = APIRouter()

# 组卷明细表：题型展示顺序（ judge → single → multiple → fill ）
_QTYPE_SORT_RANK: dict[str, int] = {"judge": 0, "single": 1, "multiple": 2, "fill": 3}

# 列表筛选：中文试卷类型与库中取值对应，便于关键字匹配
_PAPER_TYPE_CN_TO_CODE = {"正式": "formal", "模拟": "mock", "练习": "practice"}


def _normalize_paper_type_keyword(kw: str | None) -> str | None:
    if not kw:
        return None
    s = kw.strip()
    if not s:
        return None
    return _PAPER_TYPE_CN_TO_CODE.get(s, s)


def _like_metachar_escape(fragment: str) -> str:
    """LIKE 通配符转义，配合 escape='\\\\' 使用。"""
    return fragment.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _sorted_paper_items(items: list[ExamPaperItem]) -> list[ExamPaperItem]:
    """按题型升序、同题型下题号升序排列明细。"""

    def sort_key(it: ExamPaperItem) -> tuple[int, str, int, int]:
        q = it.question
        if q is None:
            return (99, "", it.sort_order, it.id)
        rank = _QTYPE_SORT_RANK.get(q.q_type, 50)
        qn = (q.question_no or "").strip()
        return (rank, qn, it.sort_order, it.id)

    return sorted(items, key=sort_key)


def _item_score_sum_by_paper(db: Session, paper_ids: list[int]) -> dict[int, Decimal]:
    """各试卷小题分值合计（用于列表总分展示）。"""
    if not paper_ids:
        return {}
    rows = db.execute(
        select(ExamPaperItem.paper_id, func.coalesce(func.sum(ExamPaperItem.score), 0))
        .where(ExamPaperItem.paper_id.in_(paper_ids))
        .group_by(ExamPaperItem.paper_id)
    ).all()
    return {int(pid): Decimal(str(s or 0)) for pid, s in rows}


def _item_count_by_paper(db: Session, paper_ids: list[int]) -> dict[int, int]:
    """各试卷已组卷题目条数。"""
    if not paper_ids:
        return {}
    rows = db.execute(
        select(ExamPaperItem.paper_id, func.count())
        .where(ExamPaperItem.paper_id.in_(paper_ids))
        .group_by(ExamPaperItem.paper_id)
    ).all()
    return {int(pid): int(c or 0) for pid, c in rows}


def _session_ref_count_by_paper(db: Session, paper_ids: list[int]) -> dict[int, int]:
    """各试卷被考试场次引用的次数。"""
    if not paper_ids:
        return {}
    rows = db.execute(
        select(ExamSession.paper_id, func.count())
        .where(ExamSession.paper_id.in_(paper_ids))
        .group_by(ExamSession.paper_id)
    ).all()
    return {int(pid): int(c or 0) for pid, c in rows}


def _gen_paper_no(db: Session, enterprise_id: int | None) -> str:
    """同一企业按日递增生成试卷编号。"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    ent = int(enterprise_id) if enterprise_id is not None else 0
    prefix = f"SJ{today}-E{ent}-"
    like = f"{prefix}%"
    n = (
        db.scalar(
            select(func.count())
            .select_from(ExamPaper)
            .where(ExamPaper.paper_no.is_not(None), ExamPaper.paper_no.like(like))
        )
        or 0
    )
    return f"{prefix}{n + 1:04d}"


def _recalc_total_score(db: Session, paper_id: int) -> None:
    s = db.scalar(
        select(func.coalesce(func.sum(ExamPaperItem.score), 0)).where(ExamPaperItem.paper_id == paper_id)
    )
    paper = db.get(ExamPaper, paper_id)
    if paper:
        paper.total_score = Decimal(str(s or 0))
        db.add(paper)


def _enterprise_for_paper(p: ExamPaper) -> tuple[int | None, str | None]:
    """所属企业：优先取关联课程的企业，否则取创建人所属企业。"""
    if p.course is not None and p.course.enterprise is not None:
        return p.course.enterprise_id, p.course.enterprise.name
    if p.creator is not None and p.creator.enterprise is not None:
        return p.creator.enterprise_id, p.creator.enterprise.name
    return None, None


def _paper_list_base_stmt():
    """列表统计与分页共用：关联创建人、课程、课程所属企业、创建人所属企业（用于按企业名称筛选）。"""
    ent_course = aliased(Enterprise)
    ent_creator = aliased(Enterprise)
    return (
        select(ExamPaper)
        .join(User, ExamPaper.created_by == User.id)
        .outerjoin(Course, ExamPaper.course_id == Course.id)
        .outerjoin(ent_course, Course.enterprise_id == ent_course.id)
        .outerjoin(ent_creator, User.enterprise_id == ent_creator.id),
        ent_course,
        ent_creator,
    )


def _apply_paper_list_keyword_filters(
    stmt,
    ent_course,
    ent_creator,
    title_keyword: str | None,
    course_keyword: str | None,
    enterprise_keyword: str | None,
    paper_type_keyword: str | None,
):
    t = (title_keyword or "").strip()
    c = (course_keyword or "").strip()
    e = (enterprise_keyword or "").strip()
    pt_raw = _normalize_paper_type_keyword(paper_type_keyword)
    if t:
        stmt = stmt.where(ExamPaper.title.like(f"%{_like_metachar_escape(t)}%", escape="\\"))
    if c:
        stmt = stmt.where(Course.name.like(f"%{_like_metachar_escape(c)}%", escape="\\"))
    if e:
        elike = f"%{_like_metachar_escape(e)}%"
        stmt = stmt.where(
            or_(
                ent_course.name.like(elike, escape="\\"),
                and_(ExamPaper.course_id.is_(None), ent_creator.name.like(elike, escape="\\")),
            )
        )
    if pt_raw:
        code = pt_raw.strip()
        if code in ("formal", "mock", "practice"):
            stmt = stmt.where(ExamPaper.paper_type == code)
        else:
            stmt = stmt.where(ExamPaper.paper_type.like(f"%{_like_metachar_escape(code)}%", escape="\\"))
    return stmt


def _assert_paper_composition_mutable(p: ExamPaper) -> None:
    """已审核试卷不允许增删题目或清空组卷。"""
    if (getattr(p, "audit_status", None) or "draft") == "reviewed":
        raise HTTPException(status_code=409, detail="已审核的试卷不可修改组卷")


def _resolve_level_name(p: ExamPaper, db: Session) -> str | None:
    """列表展示用等级名称：优先已加载关联，否则按 level_id 补查。"""
    if p.paper_level is not None:
        return p.paper_level.level_name
    if p.level_id is not None:
        pl = db.get(PaperLevel, p.level_id)
        return pl.level_name if pl else None
    return None


def _paper_summary(
    p: ExamPaper,
    db: Session,
    *,
    item_score_total: Decimal | None = None,
    item_count: int = 0,
    session_ref_count: int = 0,
) -> PaperSummary:
    eid, ename = _enterprise_for_paper(p)
    ts = item_score_total if item_score_total is not None else p.total_score
    idate = getattr(p, "issue_date", None)
    vuntil = getattr(p, "valid_until", None)
    return PaperSummary(
        id=p.id,
        title=p.title,
        paper_no=p.paper_no,
        course_id=p.course_id,
        course_name=p.course.name if p.course else None,
        paper_type=p.paper_type or "formal",
        level_id=p.level_id,
        level_name=_resolve_level_name(p, db),
        enterprise_id=eid,
        enterprise_name=ename,
        description=p.description,
        duration_minutes=p.duration_minutes,
        total_score=ts,
        item_count=item_count,
        session_ref_count=session_ref_count,
        audit_status=getattr(p, "audit_status", None) or "draft",
        issue_date=idate if isinstance(idate, date) else None,
        valid_until=vuntil if isinstance(vuntil, date) else None,
        created_by=p.created_by,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=PageResult[PaperSummary])
def list_papers(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.paper"))],
    page: Annotated[PageParams, Depends()],
    title_keyword: str | None = Query(default=None, description="试卷名称模糊匹配"),
    course_keyword: str | None = Query(default=None, description="关联课程名称模糊匹配"),
    course_id: int | None = Query(default=None, ge=1, description="按课程 ID 精确筛选（场次选卷等）"),
    enterprise_keyword: str | None = Query(default=None, description="所属企业名称模糊匹配"),
    paper_type_keyword: str | None = Query(default=None, description="试卷类型模糊匹配（如 formal、mock）"),
) -> PageResult[PaperSummary]:
    """本企业试卷列表；支持名称、课程、企业、类型模糊筛选。"""
    data_stmt, ent_course, ent_creator = _paper_list_base_stmt()
    data_stmt = restrict_exam_paper_query_by_tenant(data_stmt, db, current)
    if course_id is not None:
        data_stmt = data_stmt.where(ExamPaper.course_id == course_id)
    data_stmt = _apply_paper_list_keyword_filters(
        data_stmt, ent_course, ent_creator, title_keyword, course_keyword, enterprise_keyword, paper_type_keyword
    )

    cnt = (
        select(func.count())
        .select_from(ExamPaper)
        .join(User, ExamPaper.created_by == User.id)
        .outerjoin(Course, ExamPaper.course_id == Course.id)
        .outerjoin(ent_course, Course.enterprise_id == ent_course.id)
        .outerjoin(ent_creator, User.enterprise_id == ent_creator.id)
    )
    cnt = restrict_exam_paper_query_by_tenant(cnt, db, current)
    if course_id is not None:
        cnt = cnt.where(ExamPaper.course_id == course_id)
    cnt = _apply_paper_list_keyword_filters(
        cnt, ent_course, ent_creator, title_keyword, course_keyword, enterprise_keyword, paper_type_keyword
    )
    total = db.scalar(cnt) or 0

    rows = db.scalars(
        data_stmt.options(
            joinedload(ExamPaper.course).joinedload(Course.enterprise),
            joinedload(ExamPaper.paper_level),
            joinedload(ExamPaper.creator).joinedload(User.enterprise),
        )
        .offset(page.skip)
        .limit(page.limit)
        .order_by(ExamPaper.id.desc())
    ).all()
    pids = [r.id for r in rows]
    sums = _item_score_sum_by_paper(db, pids)
    ic = _item_count_by_paper(db, pids)
    sc = _session_ref_count_by_paper(db, pids)
    return PageResult[PaperSummary](
        total=int(total),
        items=[
            _paper_summary(
                r,
                db,
                item_score_total=sums.get(r.id, Decimal("0")),
                item_count=ic.get(r.id, 0),
                session_ref_count=sc.get(r.id, 0),
            )
            for r in rows
        ],
    )


@router.post("/batch", response_model=PaperBatchOut)
def create_papers_batch(
    body: PaperBatchCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> PaperBatchOut:
    """按题型总量自动均分并一次生成多套试卷（各套题目不重复）。"""
    course = db.get(Course, body.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, course.enterprise_id)

    if body.level_id is not None:
        pl = db.get(PaperLevel, body.level_id)
        if pl is None:
            raise HTTPException(status_code=404, detail="试卷等级不存在")
        if not is_super_role(current):
            ensure_in_managed_enterprise_scope(db, current, pl.enterprise_id)
        if pl.enterprise_id != course.enterprise_id:
            raise HTTPException(status_code=400, detail="试卷等级与课程须属同一企业")

    ent_pool = course.enterprise_id
    type_chunks: dict[str, list[list[int]]] = {}
    rule_order = [r.q_type for r in body.rules if r.total_count > 0]
    for r in body.rules:
        if r.total_count <= 0:
            continue
        type_chunks[r.q_type] = build_disjoint_chunks_for_type(
            db,
            course_id=course.id,
            enterprise_id=ent_pool,
            q_type=r.q_type,
            total=r.total_count,
            paper_count=body.paper_count,
        )
    for i in range(body.paper_count):
        tot_i = sum(len(type_chunks[qt][i]) for qt in type_chunks)
        if tot_i < 1:
            raise HTTPException(
                status_code=400,
                detail="各套试卷至少需包含 1 道题，请减少生成份数或提高某题型的总量",
            )
    per_paper_items = merge_items_in_rule_order(
        type_chunks, rule_order, body.paper_count, body.score_per, body.auto_split
    )
    summaries: list[PaperSummary] = []
    batch_meta = {
        "batch": True,
        "paper_count": body.paper_count,
        "totals": [{"q_type": r.q_type, "total_count": r.total_count} for r in body.rules],
    }
    for i in range(body.paper_count):
        title = (
            f"{body.base_title.strip()} 第{i + 1}套"
            if body.paper_count > 1
            else body.base_title.strip()
        )
        pn = _gen_paper_no(db, ent_pool)
        items_spec = per_paper_items[i]
        rules_snapshot: list[dict] = []
        for qt in rule_order:
            chunk = type_chunks[qt][i]
            if chunk:
                rules_snapshot.append(
                    {
                        "q_type": qt,
                        "use_all": False,
                        "count": len(chunk),
                        "auto_split": body.auto_split,
                        "score_per": str(body.score_per),
                    }
                )
        composition_rules = {**batch_meta, "paper_index": i, "rules_this_paper": rules_snapshot}
        p = ExamPaper(
            title=title,
            paper_no=pn,
            course_id=body.course_id,
            paper_type=(body.paper_type or "formal").strip(),
            level_id=body.level_id,
            composition_rules=composition_rules,
            description=body.description,
            duration_minutes=body.duration_minutes,
            total_score=Decimal("0"),
            issue_date=body.issue_date,
            valid_until=body.valid_until,
            created_by=current.id,
        )
        db.add(p)
        db.flush()
        for idx, (qid, score, auto_split) in enumerate(items_spec):
            db.add(
                ExamPaperItem(
                    paper_id=p.id,
                    question_id=qid,
                    sort_order=idx,
                    score=score,
                    auto_split_count=auto_split,
                )
            )
        if items_spec:
            _recalc_total_score(db, p.id)
        db.commit()
        pr = db.scalars(
            select(ExamPaper)
            .options(
                joinedload(ExamPaper.course).joinedload(Course.enterprise),
                joinedload(ExamPaper.paper_level),
                joinedload(ExamPaper.creator).joinedload(User.enterprise),
            )
            .where(ExamPaper.id == p.id)
        ).first()
        if pr is not None:
            icn = (
                db.scalar(
                    select(func.count()).select_from(ExamPaperItem).where(ExamPaperItem.paper_id == pr.id)
                )
                or 0
            )
            summaries.append(_paper_summary(pr, db, item_count=int(icn)))
    return PaperBatchOut(items=summaries)


@router.post("", response_model=PaperOut)
def create_paper(
    body: PaperCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> PaperOut:
    """新建试卷；可带组卷规则从课程题库随机抽题。"""
    course: Course | None = None
    if body.course_id is not None:
        course = db.get(Course, body.course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="课程不存在")
        if not is_super_role(current):
            ensure_in_managed_enterprise_scope(db, current, course.enterprise_id)

    if body.rules and body.course_id is None:
        raise HTTPException(status_code=400, detail="配置了组卷规则时必须指定关联课程")

    if body.level_id is not None:
        pl = db.get(PaperLevel, body.level_id)
        if pl is None:
            raise HTTPException(status_code=404, detail="试卷等级不存在")
        if not is_super_role(current):
            ensure_in_managed_enterprise_scope(db, current, pl.enterprise_id)
        if course is not None and pl.enterprise_id != course.enterprise_id:
            raise HTTPException(status_code=400, detail="试卷等级与课程须属同一企业")

    pn = (body.paper_no or "").strip() or None
    if pn:
        dup = db.scalar(select(func.count()).select_from(ExamPaper).where(ExamPaper.paper_no == pn)) or 0
        if dup:
            raise HTTPException(status_code=400, detail="试卷编号已存在")
    else:
        ent_for_no = course.enterprise_id if course is not None else current.enterprise_id
        pn = _gen_paper_no(db, ent_for_no)

    composition_rules = None
    items_spec: list[tuple[int, Decimal, int]] = []
    if body.rules:
        assert course is not None
        ent_pool = course.enterprise_id
        used: set[int] = set()
        for rule in body.rules:
            pool = fetch_question_pool_ids(db, course_id=course.id, enterprise_id=ent_pool, q_type=rule.q_type)
            picked = pick_questions_for_rule(
                pool, use_all=rule.use_all, count=rule.count, already_used=used
            )
            used.update(picked)
            for qid in picked:
                items_spec.append((qid, rule.score_per, rule.auto_split))
        composition_rules = rules_to_jsonable(body.rules)

    p = ExamPaper(
        title=body.title.strip(),
        paper_no=pn,
        course_id=body.course_id,
        paper_type=(body.paper_type or "formal").strip(),
        level_id=body.level_id,
        composition_rules=composition_rules,
        description=body.description,
        duration_minutes=body.duration_minutes,
        total_score=Decimal("0"),
        issue_date=body.issue_date,
        valid_until=body.valid_until,
        created_by=current.id,
    )
    db.add(p)
    db.flush()
    for idx, (qid, score, auto_split) in enumerate(items_spec):
        db.add(
            ExamPaperItem(
                paper_id=p.id,
                question_id=qid,
                sort_order=idx,
                score=score,
                auto_split_count=auto_split,
            )
        )
    db.commit()
    if items_spec:
        _recalc_total_score(db, p.id)
        db.commit()
    return get_paper(p.id, db, current)


def _build_paper_out(p: ExamPaper) -> PaperOut:
    items_sorted = _sorted_paper_items(list(p.items))
    items_out: list[PaperItemOut] = []
    for it in items_sorted:
        q = it.question
        items_out.append(
            PaperItemOut(
                id=it.id,
                question_id=it.question_id,
                sort_order=it.sort_order,
                score=it.score,
                auto_split_count=it.auto_split_count,
                question=QuestionOut.model_validate(q) if q else None,
            )
        )
    agg = sum((it.score for it in items_sorted), Decimal("0"))
    return PaperOut(
        id=p.id,
        title=p.title,
        paper_no=p.paper_no,
        course_id=p.course_id,
        course_name=p.course.name if p.course else None,
        paper_type=p.paper_type or "formal",
        level_id=p.level_id,
        level_name=p.paper_level.level_name if p.paper_level else None,
        composition_rules=p.composition_rules,
        description=p.description,
        duration_minutes=p.duration_minutes,
        total_score=agg,
        audit_status=getattr(p, "audit_status", None) or "draft",
        issue_date=getattr(p, "issue_date", None),
        valid_until=getattr(p, "valid_until", None),
        created_by=p.created_by,
        created_at=p.created_at,
        updated_at=p.updated_at,
        items=items_out,
    )


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(
    paper_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User,
        Depends(require_any_permission("list.paper", "action.paper.manage")),
    ],
) -> PaperOut:
    """试卷详情（含题目项与题干）。"""
    assert_paper_in_enterprise(db, current, paper_id)
    _recalc_total_score(db, paper_id)
    db.commit()
    p = db.scalars(
        select(ExamPaper)
        .options(
            joinedload(ExamPaper.items).joinedload(ExamPaperItem.question),
            joinedload(ExamPaper.course),
            joinedload(ExamPaper.paper_level),
        )
        .where(ExamPaper.id == paper_id)
    ).first()
    if p is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    return _build_paper_out(p)


@router.patch("/{paper_id}", response_model=PaperOut)
def update_paper(
    paper_id: int,
    body: PaperUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> PaperOut:
    p = assert_paper_in_enterprise(db, current, paper_id)
    data = body.model_dump(exclude_unset=True)
    if "paper_no" in data and data["paper_no"] is not None:
        pn = str(data["paper_no"]).strip()
        dup = (
            db.scalar(
                select(func.count())
                .select_from(ExamPaper)
                .where(ExamPaper.paper_no == pn, ExamPaper.id != paper_id)
            )
            or 0
        )
        if dup:
            raise HTTPException(status_code=400, detail="试卷编号已存在")
        data["paper_no"] = pn or None
    if "course_id" in data and data["course_id"] is not None:
        c = db.get(Course, data["course_id"])
        if c is None:
            raise HTTPException(status_code=404, detail="课程不存在")
        if not is_super_role(current):
            ensure_in_managed_enterprise_scope(db, current, c.enterprise_id)
    if "level_id" in data and data["level_id"] is not None:
        pl = db.get(PaperLevel, data["level_id"])
        if pl is None:
            raise HTTPException(status_code=404, detail="试卷等级不存在")
        if not is_super_role(current):
            ensure_in_managed_enterprise_scope(db, current, pl.enterprise_id)
        cid = data.get("course_id", p.course_id)
        if cid is not None:
            c2 = db.get(Course, cid)
            if c2 and pl.enterprise_id != c2.enterprise_id:
                raise HTTPException(status_code=400, detail="试卷等级与课程须属同一企业")
    for k, v in data.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return get_paper(paper_id, db, current)


@router.post("/batch-audit", response_model=dict)
def batch_audit_papers(
    body: PaperBatchIdsIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> dict:
    """批量审核：草稿改为已审核。"""
    n_ok = 0
    for pid in body.ids:
        p = db.get(ExamPaper, pid)
        if p is None:
            continue
        try:
            assert_paper_in_enterprise(db, current, pid)
        except HTTPException:
            continue
        if (getattr(p, "audit_status", None) or "draft") != "draft":
            continue
        p.audit_status = "reviewed"
        n_ok += 1
    db.commit()
    return {"updated": n_ok}


@router.post("/batch-unaudit", response_model=dict)
def batch_unaudit_papers(
    body: PaperBatchIdsIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> dict:
    """批量反审核：已审核改为草稿；已被考试场次引用的试卷跳过。"""
    n_ok = 0
    for pid in body.ids:
        p = db.get(ExamPaper, pid)
        if p is None:
            continue
        try:
            assert_paper_in_enterprise(db, current, pid)
        except HTTPException:
            continue
        if (getattr(p, "audit_status", None) or "draft") != "reviewed":
            continue
        n_sess = (
            db.scalar(select(func.count()).select_from(ExamSession).where(ExamSession.paper_id == pid)) or 0
        )
        if int(n_sess) > 0:
            continue
        p.audit_status = "draft"
        n_ok += 1
    db.commit()
    return {"updated": n_ok}


@router.delete("/{paper_id}", status_code=204)
def delete_paper(
    paper_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> None:
    p = assert_paper_in_enterprise(db, current, paper_id)
    if (getattr(p, "audit_status", None) or "draft") == "reviewed":
        raise HTTPException(status_code=409, detail="已审核的试卷不可删除")
    db.delete(p)
    db.commit()


@router.delete("/{paper_id}/items", status_code=204)
def clear_paper_items(
    paper_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> None:
    """反组卷：清空试卷内全部题目。"""
    p = assert_paper_in_enterprise(db, current, paper_id)
    _assert_paper_composition_mutable(p)
    db.execute(delete(ExamPaperItem).where(ExamPaperItem.paper_id == paper_id))
    _recalc_total_score(db, paper_id)
    db.commit()


@router.post("/{paper_id}/items", response_model=PaperOut)
def add_paper_item(
    paper_id: int,
    body: PaperItemAdd,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> PaperOut:
    """向试卷添加一题。"""
    p = assert_paper_in_enterprise(db, current, paper_id)
    _assert_paper_composition_mutable(p)
    q = assert_question_in_enterprise(db, current, body.question_id)
    if q.status != "published":
        raise HTTPException(
            status_code=400,
            detail="仅已发布题目可加入试卷；草稿请先发布，已禁用题目不可组卷",
        )
    dup = db.scalar(
        select(func.count())
        .select_from(ExamPaperItem)
        .where(
            ExamPaperItem.paper_id == paper_id,
            ExamPaperItem.question_id == body.question_id,
        )
    )
    if dup:
        raise HTTPException(status_code=400, detail="该题已在试卷中")
    it = ExamPaperItem(
        paper_id=paper_id,
        question_id=body.question_id,
        sort_order=body.sort_order,
        score=body.score,
        auto_split_count=body.auto_split_count,
    )
    db.add(it)
    db.commit()
    _recalc_total_score(db, paper_id)
    db.commit()
    return get_paper(paper_id, db, current)


@router.delete("/{paper_id}/items/{item_id}", status_code=204)
def remove_paper_item(
    paper_id: int,
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> None:
    """从试卷移除题目项。"""
    p = assert_paper_in_enterprise(db, current, paper_id)
    _assert_paper_composition_mutable(p)
    it = db.get(ExamPaperItem, item_id)
    if it is None or it.paper_id != paper_id:
        raise HTTPException(status_code=404, detail="试卷题目项不存在")
    db.delete(it)
    db.commit()
    _recalc_total_score(db, paper_id)
    db.commit()
