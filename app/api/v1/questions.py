# -*- coding: utf-8 -*-

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.question import Question
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.question import QuestionCreate, QuestionOut, QuestionUpdate

router = APIRouter()


@router.get("", response_model=PageResult[QuestionOut])
def list_questions(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
    page: Annotated[PageParams, Depends()],
    q_type: str | None = None,
    status: str | None = None,
) -> PageResult[QuestionOut]:
    """题目列表。"""
    stmt = select(func.count()).select_from(Question)
    if q_type:
        stmt = stmt.where(Question.q_type == q_type)
    if status:
        stmt = stmt.where(Question.status == status)
    total = db.scalar(stmt) or 0
    q = select(Question)
    if q_type:
        q = q.where(Question.q_type == q_type)
    if status:
        q = q.where(Question.status == status)
    rows = db.scalars(q.offset(page.skip).limit(page.limit).order_by(Question.id.desc())).all()
    return PageResult[QuestionOut](total=int(total), items=[QuestionOut.model_validate(r) for r in rows])


@router.post("", response_model=QuestionOut)
def create_question(
    body: QuestionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> QuestionOut:
    """新增题目。"""
    obj = Question(
        q_type=body.q_type,
        stem=body.stem,
        options_json=body.options_json,
        answer_json=body.answer_json,
        analysis=body.analysis,
        difficulty=body.difficulty,
        status=body.status,
        created_by=current.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return QuestionOut.model_validate(obj)


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(
    question_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> QuestionOut:
    obj = db.get(Question, question_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    return QuestionOut.model_validate(obj)


@router.patch("/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    body: QuestionUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> QuestionOut:
    obj = db.get(Question, question_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return QuestionOut.model_validate(obj)


@router.delete("/{question_id}", status_code=204)
def delete_question(
    question_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("admin", "teacher"))],
) -> None:
    obj = db.get(Question, question_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    db.delete(obj)
    db.commit()
