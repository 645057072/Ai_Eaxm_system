# -*- coding: utf-8 -*-
"""考生进入考试、交卷时与 exam_candidate 档案同步。"""

from datetime import datetime, timezone
from typing import Optional

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exam import ExamAttempt, ExamPaper, ExamSession
from app.models.exam_candidate import ExamCandidate
from app.models.student import Student
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
    """用户进入考试后自动建档或更新最近作答。

    - 优先使用 user.student_id
    - 若未绑定学员，尝试按 student_no==username 自动匹配（同企业）
    """
    stu_id = user.student_id
    if not stu_id and user.enterprise_id:
        s = db.scalars(
            select(Student).where(Student.enterprise_id == user.enterprise_id, Student.student_no == user.username)
        ).first()
        if s is not None:
            stu_id = s.id
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
            ExamCandidate.student_id == stu_id,
        )
    ).first()
    if ec:
        ec.session_id = session.id
        ec.last_attempt_id = attempt_id
        return
    if not stu_id:
        return
    db.add(
        ExamCandidate(
            exam_no=exam_no,
            enterprise_id=ent_id,
            course_id=course_id,
            student_id=stu_id,
            session_id=session.id,
            last_attempt_id=attempt_id,
        )
    )


def update_exam_candidate_after_submit(db: Session, att: ExamAttempt) -> None:
    """交卷后写入作答时长、得分与是否及格，并关联作答记录。

    若考生记录不存在，会尝试补建（同 ensure_exam_candidate_for_session 的学员匹配策略）。
    """
    u = db.get(User, att.user_id)
    if u is None:
        return
    stu_id = u.student_id
    if not stu_id and u.enterprise_id:
        s = db.scalars(
            select(Student).where(Student.enterprise_id == u.enterprise_id, Student.student_no == u.username)
        ).first()
        if s is not None:
            stu_id = s.id
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
            ExamCandidate.student_id == stu_id,
        )
    ).first()
    if ec is None:
        paper = sess.paper or db.get(ExamPaper, sess.paper_id)
        course_id = sess.course_id or (paper.course_id if paper else None)
        if not stu_id or course_id is None:
            return
        ec = ExamCandidate(
            exam_no=exam_no,
            enterprise_id=sess.enterprise_id,
            course_id=int(course_id),
            student_id=int(stu_id),
            session_id=sess.id,
            last_attempt_id=att.id,
        )
        db.add(ec)
    ec.last_attempt_id = att.id
    ec.session_id = sess.id
    if att.submitted_at and att.started_at:
        sa = _dt_as_utc(att.submitted_at)
        sb = _dt_as_utc(att.started_at)
        ec.answer_duration_seconds = max(0, int((sa - sb).total_seconds()))
    if att.total_score is not None:
        ec.score = att.total_score
        paper = sess.paper or db.get(ExamPaper, sess.paper_id)
        pass_line = (paper.pass_score if paper and paper.pass_score is not None else Decimal("0"))
        ec.passed = Decimal(str(att.total_score)) >= pass_line
