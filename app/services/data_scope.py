# -*- coding: utf-8 -*-
"""按所属企业过滤数据的通用约束。"""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import false
from sqlalchemy.orm import Session

from app.core.permissions import is_super_role
from app.models.exam import ExamPaper, ExamSession
from app.models.question import Question
from app.models.user import User


def ensure_same_enterprise(current: User, target_enterprise_id: int | None) -> None:
    """校验资源所属企业与当前用户一致；内置管理员不受限。"""
    if is_super_role(current):
        return
    if current.enterprise_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号未关联企业")
    if target_enterprise_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该资源")
    if current.enterprise_id != target_enterprise_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问其他企业数据")


def enterprise_filter_value(user: User) -> int | None:
    return user.enterprise_id


def restrict_query_by_creator_enterprise(query: Any, current: User, user_model: type[User] = User) -> Any:
    """连表查询中按创建者所属企业限制；超管不限。用于题目/试卷/场次等列表。"""
    if is_super_role(current):
        return query
    if current.enterprise_id is None:
        return query.where(false())
    return query.where(user_model.enterprise_id == current.enterprise_id)


def _creator_enterprise(db: Session, user_id: int | None) -> int | None:
    if user_id is None:
        return None
    u = db.get(User, user_id)
    return u.enterprise_id if u else None


def assert_question_in_enterprise(db: Session, current: User, question_id: int) -> Question:
    obj = db.get(Question, question_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    if is_super_role(current):
        return obj
    ce = _creator_enterprise(db, obj.created_by)
    if ce is None or ce != current.enterprise_id:
        raise HTTPException(status_code=403, detail="题目不在本企业范围内")
    return obj


def assert_paper_in_enterprise(db: Session, current: User, paper_id: int) -> ExamPaper:
    p = db.get(ExamPaper, paper_id)
    if p is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    if is_super_role(current):
        return p
    ce = _creator_enterprise(db, p.created_by)
    if ce is None or ce != current.enterprise_id:
        raise HTTPException(status_code=403, detail="试卷不在本企业范围内")
    return p


def assert_session_in_enterprise(db: Session, current: User, session_id: int) -> ExamSession:
    s = db.get(ExamSession, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="场次不存在")
    if is_super_role(current):
        return s
    ce = _creator_enterprise(db, s.created_by)
    if ce is None or ce != current.enterprise_id:
        raise HTTPException(status_code=403, detail="考试场次不在本企业范围内")
    return s
