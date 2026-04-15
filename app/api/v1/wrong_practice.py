# -*- coding: utf-8 -*-
"""错题练习：列表、单题练习、提交判定。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.exam_wrong_question import ExamWrongQuestion
from app.models.question import Question
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.wrong_practice import (
    WrongAnswerIn,
    WrongAnswerResultOut,
    WrongCourseRow,
    WrongQuestionOut,
)
from app.services.grading import is_correct
from app.services.wrong_question_sync import count_wrong_by_course, has_wrong_question

router = APIRouter(prefix="/wrong-practice", tags=["错题练习"])


@router.get("", response_model=PageResult[WrongCourseRow])
def list_wrong_courses(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.exam.take"))],
    page: Annotated[PageParams, Depends()],
    keyword: str | None = Query(default=None, description="课程名称模糊"),
) -> PageResult[WrongCourseRow]:
    """错题练习列表（按课程汇总）。"""
    if current.enterprise_id is None:
        return PageResult[WrongCourseRow](total=0, items=[])

    kw = (keyword or "").strip()
    w = []
    w.append(ExamWrongQuestion.enterprise_id == current.enterprise_id)
    w.append(ExamWrongQuestion.user_id == current.id)
    if kw:
        w.append(Course.name.like(f"%{kw}%"))
    cond = and_(*w)

    base = (
        select(
            ExamWrongQuestion.course_id,
            func.count().label("wrong_count"),
            Course.name,
            ExamWrongQuestion.enterprise_id,
            Enterprise.name,
        )
        .outerjoin(Course, ExamWrongQuestion.course_id == Course.id)
        .outerjoin(Enterprise, ExamWrongQuestion.enterprise_id == Enterprise.id)
        .where(cond)
        .group_by(
            ExamWrongQuestion.course_id,
            Course.name,
            ExamWrongQuestion.enterprise_id,
            Enterprise.name,
        )
    )
    cnt = select(func.count()).select_from(base.subquery())
    total = int(db.scalar(cnt) or 0)
    rows = db.execute(base.offset(page.skip).limit(page.limit).order_by(func.count().desc())).all()
    items = [
        WrongCourseRow(
            course_id=int(cid),
            course_name=cname or "—",
            enterprise_id=int(eid),
            enterprise_name=ename or "—",
            wrong_count=int(wc),
        )
        for cid, wc, cname, eid, ename in rows
    ]
    return PageResult[WrongCourseRow](total=total, items=items)


@router.get("/{course_id}/next", response_model=WrongQuestionOut)
def get_next_wrong_question(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.exam.take"))],
) -> WrongQuestionOut:
    """取下一题（按加入时间先后）。"""
    if current.enterprise_id is None:
        raise HTTPException(status_code=400, detail="当前账号未关联企业")

    row = db.scalars(
        select(ExamWrongQuestion)
        .where(
            ExamWrongQuestion.enterprise_id == current.enterprise_id,
            ExamWrongQuestion.user_id == current.id,
            ExamWrongQuestion.course_id == course_id,
        )
        .order_by(ExamWrongQuestion.id.asc())
        .limit(1)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="暂无错题")
    q = db.get(Question, row.question_id)
    if q is None:
        db.execute(delete(ExamWrongQuestion).where(ExamWrongQuestion.id == row.id))
        db.commit()
        raise HTTPException(status_code=404, detail="题目已删除")
    rem = count_wrong_by_course(db, enterprise_id=current.enterprise_id, user_id=current.id, course_id=course_id)
    return WrongQuestionOut(
        course_id=course_id,
        question_id=q.id,
        q_type=q.q_type,
        stem=q.stem,
        options_json=q.options_json,
        remaining=rem,
    )


@router.post("/{course_id}/submit", response_model=WrongAnswerResultOut)
def submit_wrong_answer(
    course_id: int,
    body: WrongAnswerIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.exam.take"))],
) -> WrongAnswerResultOut:
    """提交作答：展示标准答案与解析；答对后移除错题集。"""
    if current.enterprise_id is None:
        raise HTTPException(status_code=400, detail="当前账号未关联企业")
    q = db.get(Question, body.question_id)
    if q is None:
        raise HTTPException(status_code=404, detail="题目不存在")

    if not has_wrong_question(
        db,
        enterprise_id=current.enterprise_id,
        user_id=current.id,
        course_id=course_id,
        question_id=body.question_id,
    ):
        raise HTTPException(status_code=400, detail="该题不在当前错题集中")

    ok = is_correct(q, body.user_answer_json)
    removed = False
    if ok:
        # 仅移除当前课程下的错题条目
        db.execute(
            delete(ExamWrongQuestion).where(
                ExamWrongQuestion.enterprise_id == current.enterprise_id,
                ExamWrongQuestion.user_id == current.id,
                ExamWrongQuestion.course_id == course_id,
                ExamWrongQuestion.question_id == body.question_id,
            )
        )
        removed = True
        db.commit()

    rem = count_wrong_by_course(db, enterprise_id=current.enterprise_id, user_id=current.id, course_id=course_id)
    return WrongAnswerResultOut(
        question_id=body.question_id,
        correct=bool(ok),
        std_answer_json=q.answer_json,
        analysis=q.analysis,
        removed_from_wrong_set=removed,
        remaining=rem,
    )

