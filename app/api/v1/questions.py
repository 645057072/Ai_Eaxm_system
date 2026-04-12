# -*- coding: utf-8 -*-

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_any_permission, require_permission
from app.models.question import Question
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.question import QuestionCreate, QuestionOut, QuestionUpdate
from app.services.data_scope import assert_question_in_enterprise

router = APIRouter()


@router.get("", response_model=PageResult[QuestionOut])
def list_questions(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.question"))],
    page: Annotated[PageParams, Depends()],
    q_type: str | None = None,
    status: str | None = None,
) -> PageResult[QuestionOut]:
    """本企业用户创建的题目列表。"""
    stmt = (
        select(func.count())
        .select_from(Question)
        .join(User, Question.created_by == User.id)
        .where(User.enterprise_id == current.enterprise_id)
    )
    if q_type:
        stmt = stmt.where(Question.q_type == q_type)
    if status:
        stmt = stmt.where(Question.status == status)
    total = db.scalar(stmt) or 0
    q = (
        select(Question)
        .join(User, Question.created_by == User.id)
        .where(User.enterprise_id == current.enterprise_id)
    )
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
    current: Annotated[User, Depends(require_permission("action.question.manage"))],
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
    current: Annotated[
        User,
        Depends(require_any_permission("list.question", "action.question.manage")),
    ],
) -> QuestionOut:
    obj = assert_question_in_enterprise(db, current, question_id)
    return QuestionOut.model_validate(obj)


@router.patch("/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    body: QuestionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.manage"))],
) -> QuestionOut:
    obj = assert_question_in_enterprise(db, current, question_id)
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
    current: Annotated[User, Depends(require_permission("action.question.manage"))],
) -> None:
    obj = assert_question_in_enterprise(db, current, question_id)
    db.delete(obj)
    db.commit()
