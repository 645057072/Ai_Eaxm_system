# -*- coding: utf-8 -*-
"""按课程题库与题型规则抽取题目（无放回）。"""

import random
from typing import List, Set

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.question import Question


def fetch_question_pool_ids(
    db: Session,
    *,
    course_id: int,
    enterprise_id: int,
    q_type: str,
) -> List[int]:
    """课程+企业下已发布题目的指定题型 id 列表。"""
    rows = db.scalars(
        select(Question.id).where(
            Question.course_id == course_id,
            Question.enterprise_id == enterprise_id,
            Question.q_type == q_type,
            Question.status == "published",
        )
    ).all()
    return list(rows)


def pick_questions_for_rule(
    pool: List[int],
    *,
    use_all: bool,
    count: int,
    already_used: Set[int],
) -> List[int]:
    """从候选池中无放回抽样；全选时取池中尚未使用的全部题目。"""
    free = [i for i in pool if i not in already_used]
    if use_all:
        return free
    if count > len(free):
        raise HTTPException(
            status_code=400,
            detail=f"该题型在题库区间内可用题目 {len(free)} 道，少于要求的 {count} 道",
        )
    random.shuffle(free)
    return free[:count]


def rules_to_jsonable(rules: list) -> list:
    """组卷规则存库用（Decimal 等可序列化）。"""
    out: list = []
    for r in rules:
        d = r.model_dump(mode="json")
        out.append(d)
    return out
