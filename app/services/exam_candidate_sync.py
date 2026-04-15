# -*- coding: utf-8 -*-
"""考生进入考试、交卷时与 exam_candidate 档案同步。"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exam import ExamAttempt, ExamPaper, ExamSession
from app.models.exam_candidate import ExamCandidate
from app.models.user import User


def _dt_as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def ensure_exam_candidate_for_session(
    db: Session,
    session: ExamSession,
    user: User,
    attempt_id: int,
) -> None:
    """用户进入考试后自动建档或更新最近作答（需用户已关联学员）。"""
    if not user.student_id:
        return
    paper: Optional[ExamPaper] = session.paper
    if paper is None and session.paper_id:
        paper = db.get(ExamPaper, session.paper_id)
    course_id = session.course_id or (paper.course_id if paper else None)
    if course_id is None:
        return
    exam_no = (session.session_code or "").strip() or f"SESS{session.id}"
    ent_id = session.enterprise_id
    ec = db.scalars(
        select(ExamCandidate).where(
            ExamCandidate.enterprise_id == ent_id,
            ExamCandidate.exam_no == exam_no,
            ExamCandidate.student_id == user.student_id,
        )
    ).first()
    if ec:
        ec.session_id = session.id
        ec.last_attempt_id = attempt_id
        return
    db.add(
        ExamCandidate(
            exam_no=exam_no,
            enterprise_id=ent_id,
            course_id=course_id,
            student_id=user.student_id,
            session_id=session.id,
            last_attempt_id=attempt_id,
        )
    )


def update_exam_candidate_after_submit(db: Session, att: ExamAttempt) -> None:
    """交卷后写入作答时长并关联作答记录。"""
    u = db.get(User, att.user_id)
    if u is None or not u.student_id:
        return
    sess = att.session
    if sess is None:
        sess = db.get(ExamSession, att.session_id)
    if sess is None:
        return
    exam_no = (sess.session_code or "").strip() or f"SESS{sess.id}"
    ec = db.scalars(
        select(ExamCandidate).where(
            ExamCandidate.enterprise_id == sess.enterprise_id,
            ExamCandidate.exam_no == exam_no,
            ExamCandidate.student_id == u.student_id,
        )
    ).first()
    if ec is None:
        return
    ec.last_attempt_id = att.id
    ec.session_id = sess.id
    if att.submitted_at and att.started_at:
        sa = _dt_as_utc(att.submitted_at)
        sb = _dt_as_utc(att.started_at)
        ec.answer_duration_seconds = max(0, int((sa - sb).total_seconds()))
