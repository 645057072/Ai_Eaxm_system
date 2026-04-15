# -*- coding: utf-8 -*-
"""按所属企业过滤数据的通用约束。"""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import and_, false, or_, select
from sqlalchemy.orm import Session

from app.core.permissions import is_enterprise_scope_admin, is_super_role
from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.exam import ExamPaper, ExamSession
from app.models.question import Question
from app.models.user import User


def collect_descendant_enterprise_ids(db: Session, root_id: int) -> set[int]:
    """自 root_id 起向下收集本节点及全部下级企业 ID（不限层级）。"""
    result: set[int] = {root_id}
    frontier: list[int] = [root_id]
    while frontier:
        batch = frontier
        frontier = []
        child_ids = db.scalars(select(Enterprise.id).where(Enterprise.parent_id.in_(batch))).all()
        for cid in child_ids:
            if cid not in result:
                result.add(cid)
                frontier.append(cid)
    return result


def get_managed_enterprise_ids(db: Session, current: User) -> set[int] | None:
    """超管返回 None 表示不按企业过滤；其余返回可访问的企业 ID 集合（空集表示无任何数据）。"""
    if is_super_role(current):
        return None
    if current.enterprise_id is None:
        return set()
    if is_enterprise_scope_admin(current):
        return collect_descendant_enterprise_ids(db, current.enterprise_id)
    return {current.enterprise_id}


def ensure_in_managed_enterprise_scope(db: Session, current: User, target_enterprise_id: int | None) -> None:
    """校验目标企业是否在当前用户可管理的企业范围内。"""
    if is_super_role(current):
        return
    if target_enterprise_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该资源")
    managed = get_managed_enterprise_ids(db, current)
    if not managed or target_enterprise_id not in managed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问其他企业数据")


def enterprise_is_under_ancestor(db: Session, ancestor_id: int, node_id: int) -> bool:
    """判断 node 是否位于 ancestor 的子树中（含 node==ancestor）。"""
    cur: int | None = node_id
    for _ in range(10000):
        if cur == ancestor_id:
            return True
        if cur is None:
            return False
        row = db.get(Enterprise, cur)
        if row is None:
            return False
        cur = row.parent_id
    return False


def restrict_query_by_creator_enterprise(
    query: Any, db: Session, current: User, user_model: type[User] = User
) -> Any:
    """连表查询中按创建者所属企业限制；超管不限。"""
    if is_super_role(current):
        return query
    managed = get_managed_enterprise_ids(db, current)
    if not managed:
        return query.where(false())
    return query.where(user_model.enterprise_id.in_(managed))


def restrict_questions_query_by_tenant(
    query: Any, db: Session, current: User, creator_user: type[User] = User
) -> Any:
    """题目列表：优先按题目 enterprise_id 归属；旧数据 enterprise_id 为空时按创建者企业。"""
    if is_super_role(current):
        return query
    managed = get_managed_enterprise_ids(db, current)
    if not managed:
        return query.where(false())
    return query.where(
        or_(
            Question.enterprise_id.in_(managed),
            and_(Question.enterprise_id.is_(None), creator_user.enterprise_id.in_(managed)),
        )
    )


def restrict_exam_paper_query_by_tenant(
    query: Any, db: Session, current: User, creator_user: type[User] = User
) -> Any:
    """试卷列表：有关联课程时按课程所属企业；无课程时按创建者企业。"""
    if is_super_role(current):
        return query
    managed = get_managed_enterprise_ids(db, current)
    if not managed:
        return query.where(false())
    return query.where(
        or_(
            Course.enterprise_id.in_(managed),
            and_(ExamPaper.course_id.is_(None), creator_user.enterprise_id.in_(managed)),
        )
    )


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
    managed = get_managed_enterprise_ids(db, current)
    if not managed:
        raise HTTPException(status_code=403, detail="账号未关联企业")
    if obj.enterprise_id is not None:
        if obj.enterprise_id not in managed:
            raise HTTPException(status_code=403, detail="题目不在本企业范围内")
        return obj
    ce = _creator_enterprise(db, obj.created_by)
    if ce is None or ce not in managed:
        raise HTTPException(status_code=403, detail="题目不在本企业范围内")
    return obj


def assert_paper_in_enterprise(db: Session, current: User, paper_id: int) -> ExamPaper:
    p = db.get(ExamPaper, paper_id)
    if p is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    if is_super_role(current):
        return p
    managed = get_managed_enterprise_ids(db, current)
    if not managed:
        raise HTTPException(status_code=403, detail="账号未关联企业")
    if p.course_id is not None:
        c = db.get(Course, p.course_id)
        if c is not None and c.enterprise_id in managed:
            return p
    ce = _creator_enterprise(db, p.created_by)
    if ce is not None and ce in managed:
        return p
    raise HTTPException(status_code=403, detail="试卷不在本企业范围内")


def assert_session_in_enterprise(db: Session, current: User, session_id: int) -> ExamSession:
    s = db.get(ExamSession, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="场次不存在")
    if is_super_role(current):
        return s
    assert_paper_in_enterprise(db, current, s.paper_id)
    return s


def session_list_tenant_filter(PaperCreator: Any, db: Session, current: User) -> Any:
    """考试场次列表：课程企业或仅按创建者企业归属的试卷，限定在可管理企业集合内。"""
    if is_super_role(current):
        return None
    managed = get_managed_enterprise_ids(db, current)
    if not managed:
        return false()
    return or_(
        Course.enterprise_id.in_(managed),
        and_(ExamPaper.course_id.is_(None), PaperCreator.enterprise_id.in_(managed)),
    )
