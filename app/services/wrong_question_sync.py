# -*- coding: utf-8 -*-
"""错题集同步：交卷写入错题/未答题；答对移除。"""

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from app.models.exam_wrong_question import ExamWrongQuestion


def upsert_wrong_question(
    db: Session,
    *,
    enterprise_id: int,
    user_id: int,
    course_id: int,
    question_id: int,
) -> None:
    """写入错题集（已存在则更新时间）。"""
    stmt = insert(ExamWrongQuestion).values(
        enterprise_id=enterprise_id,
        user_id=user_id,
        course_id=course_id,
        question_id=question_id,
    )
    # MySQL: on duplicate key update
    stmt = stmt.on_duplicate_key_update(question_id=stmt.inserted.question_id)
    db.execute(stmt)


def has_wrong_question(
    db: Session,
    *,
    enterprise_id: int,
    user_id: int,
    course_id: int,
    question_id: int,
) -> bool:
    return (
        db.scalar(
            select(func.count())
            .select_from(ExamWrongQuestion)
            .where(
                ExamWrongQuestion.enterprise_id == enterprise_id,
                ExamWrongQuestion.user_id == user_id,
                ExamWrongQuestion.course_id == course_id,
                ExamWrongQuestion.question_id == question_id,
            )
        )
        or 0
    ) > 0


def remove_wrong_question(
    db: Session,
    *,
    enterprise_id: int,
    user_id: int,
    course_id: int,
    question_id: int,
) -> None:
    db.execute(
        delete(ExamWrongQuestion).where(
            ExamWrongQuestion.enterprise_id == enterprise_id,
            ExamWrongQuestion.user_id == user_id,
            ExamWrongQuestion.course_id == course_id,
            ExamWrongQuestion.question_id == question_id,
        )
    )


def count_wrong_by_course(db: Session, *, enterprise_id: int, user_id: int, course_id: int) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(ExamWrongQuestion)
            .where(
                ExamWrongQuestion.enterprise_id == enterprise_id,
                ExamWrongQuestion.user_id == user_id,
                ExamWrongQuestion.course_id == course_id,
            )
        )
        or 0
    )

