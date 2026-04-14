# -*- coding: utf-8 -*-
"""试卷：组卷与题目项维护。"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.permissions import is_super_role
from app.models.course import Course
from app.models.exam import ExamPaper, ExamPaperItem
from app.models.paper_level import PaperLevel
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.paper import (
    PaperBatchCreate,
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
    ensure_same_enterprise,
    restrict_exam_paper_query_by_tenant,
)
from app.services.paper_batch import build_disjoint_chunks_for_type, merge_items_in_rule_order
from app.services.paper_compose import fetch_question_pool_ids, pick_questions_for_rule, rules_to_jsonable

router = APIRouter()


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


def _paper_summary(p: ExamPaper) -> PaperSummary:
    eid, ename = _enterprise_for_paper(p)
    return PaperSummary(
        id=p.id,
        title=p.title,
        paper_no=p.paper_no,
        course_id=p.course_id,
        course_name=p.course.name if p.course else None,
        paper_type=p.paper_type or "formal",
        level_id=p.level_id,
        level_name=p.paper_level.level_name if p.paper_level else None,
        enterprise_id=eid,
        enterprise_name=ename,
        description=p.description,
        duration_minutes=p.duration_minutes,
        total_score=p.total_score,
        created_by=p.created_by,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=PageResult[PaperSummary])
def list_papers(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.paper"))],
    page: Annotated[PageParams, Depends()],
) -> PageResult[PaperSummary]:
    """本企业试卷列表。"""
    cnt = (
        select(func.count())
        .select_from(ExamPaper)
        .join(User, ExamPaper.created_by == User.id)
        .outerjoin(Course, ExamPaper.course_id == Course.id)
    )
    cnt = restrict_exam_paper_query_by_tenant(cnt, current)
    total = db.scalar(cnt) or 0
    rows = db.scalars(
        restrict_exam_paper_query_by_tenant(
            select(ExamPaper)
            .join(User, ExamPaper.created_by == User.id)
            .outerjoin(Course, ExamPaper.course_id == Course.id),
            current,
        )
        .options(
            joinedload(ExamPaper.course).joinedload(Course.enterprise),
            joinedload(ExamPaper.paper_level),
            joinedload(ExamPaper.creator).joinedload(User.enterprise),
        )
        .offset(page.skip)
        .limit(page.limit)
        .order_by(ExamPaper.id.desc())
    ).all()
    return PageResult[PaperSummary](total=int(total), items=[_paper_summary(r) for r in rows])


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
        ensure_same_enterprise(current, course.enterprise_id)

    if body.level_id is not None:
        pl = db.get(PaperLevel, body.level_id)
        if pl is None:
            raise HTTPException(status_code=404, detail="试卷等级不存在")
        if not is_super_role(current):
            ensure_same_enterprise(current, pl.enterprise_id)
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
            summaries.append(_paper_summary(pr))
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
            ensure_same_enterprise(current, course.enterprise_id)

    if body.rules and body.course_id is None:
        raise HTTPException(status_code=400, detail="配置了组卷规则时必须指定关联课程")

    if body.level_id is not None:
        pl = db.get(PaperLevel, body.level_id)
        if pl is None:
            raise HTTPException(status_code=404, detail="试卷等级不存在")
        if not is_super_role(current):
            ensure_same_enterprise(current, pl.enterprise_id)
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
    items_out: list[PaperItemOut] = []
    for it in sorted(p.items, key=lambda x: (x.sort_order, x.id)):
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
        total_score=p.total_score,
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
            ensure_same_enterprise(current, c.enterprise_id)
    if "level_id" in data and data["level_id"] is not None:
        pl = db.get(PaperLevel, data["level_id"])
        if pl is None:
            raise HTTPException(status_code=404, detail="试卷等级不存在")
        if not is_super_role(current):
            ensure_same_enterprise(current, pl.enterprise_id)
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


@router.delete("/{paper_id}", status_code=204)
def delete_paper(
    paper_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> None:
    p = assert_paper_in_enterprise(db, current, paper_id)
    db.delete(p)
    db.commit()


@router.post("/{paper_id}/items", response_model=PaperOut)
def add_paper_item(
    paper_id: int,
    body: PaperItemAdd,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.paper.manage"))],
) -> PaperOut:
    """向试卷添加一题。"""
    assert_paper_in_enterprise(db, current, paper_id)
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
    assert_paper_in_enterprise(db, current, paper_id)
    it = db.get(ExamPaperItem, item_id)
    if it is None or it.paper_id != paper_id:
        raise HTTPException(status_code=404, detail="试卷题目项不存在")
    db.delete(it)
    db.commit()
    _recalc_total_score(db, paper_id)
    db.commit()
