# -*- coding: utf-8 -*-
"""试卷：组卷与题目项维护。"""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_roles
from app.models.exam import ExamPaper, ExamPaperItem
from app.models.question import Question
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.paper import PaperCreate, PaperItemAdd, PaperItemOut, PaperOut, PaperSummary, PaperUpdate
from app.schemas.question import QuestionOut

router = APIRouter()


def _recalc_total_score(db: Session, paper_id: int) -> None:
    s = db.scalar(
        select(func.coalesce(func.sum(ExamPaperItem.score), 0)).where(ExamPaperItem.paper_id == paper_id)
    )
    paper = db.get(ExamPaper, paper_id)
    if paper:
        paper.total_score = Decimal(str(s or 0))
        db.add(paper)


@router.get("", response_model=PageResult[PaperSummary])
def list_papers(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
    page: Annotated[PageParams, Depends()],
) -> PageResult[PaperSummary]:
    """试卷列表（不含小题明细，减少负载）。"""
    total = db.scalar(select(func.count()).select_from(ExamPaper)) or 0
    rows = db.scalars(
        select(ExamPaper).offset(page.skip).limit(page.limit).order_by(ExamPaper.id.desc())
    ).all()
    return PageResult[PaperSummary](total=int(total), items=[PaperSummary.model_validate(r) for r in rows])


@router.post("", response_model=PaperOut)
def create_paper(
    body: PaperCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> PaperOut:
    """新建试卷。"""
    p = ExamPaper(
        title=body.title,
        description=body.description,
        duration_minutes=body.duration_minutes,
        total_score=Decimal("0"),
        created_by=current.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return PaperOut.model_validate(p)


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(
    paper_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> PaperOut:
    """试卷详情（含题目项与题干）。"""
    p = db.scalars(
        select(ExamPaper)
        .options(joinedload(ExamPaper.items).joinedload(ExamPaperItem.question))
        .where(ExamPaper.id == paper_id)
    ).first()
    if p is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    items_out: list[PaperItemOut] = []
    for it in sorted(p.items, key=lambda x: (x.sort_order, x.id)):
        q = it.question
        items_out.append(
            PaperItemOut(
                id=it.id,
                question_id=it.question_id,
                sort_order=it.sort_order,
                score=it.score,
                question=QuestionOut.model_validate(q) if q else None,
            )
        )
    return PaperOut(
        id=p.id,
        title=p.title,
        description=p.description,
        duration_minutes=p.duration_minutes,
        total_score=p.total_score,
        created_by=p.created_by,
        created_at=p.created_at,
        updated_at=p.updated_at,
        items=items_out,
    )


@router.patch("/{paper_id}", response_model=PaperOut)
def update_paper(
    paper_id: int,
    body: PaperUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> PaperOut:
    p = db.get(ExamPaper, paper_id)
    if p is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return PaperOut.model_validate(p)


@router.delete("/{paper_id}", status_code=204)
def delete_paper(
    paper_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> None:
    p = db.get(ExamPaper, paper_id)
    if p is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    db.delete(p)
    db.commit()


@router.post("/{paper_id}/items", response_model=PaperOut)
def add_paper_item(
    paper_id: int,
    body: PaperItemAdd,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> PaperOut:
    """向试卷添加一题。"""
    p = db.get(ExamPaper, paper_id)
    if p is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    if db.get(Question, body.question_id) is None:
        raise HTTPException(status_code=400, detail="题目不存在")
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
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> None:
    """从试卷移除题目项。"""
    it = db.get(ExamPaperItem, item_id)
    if it is None or it.paper_id != paper_id:
        raise HTTPException(status_code=404, detail="试卷题目项不存在")
    db.delete(it)
    db.commit()
    _recalc_total_score(db, paper_id)
    db.commit()
