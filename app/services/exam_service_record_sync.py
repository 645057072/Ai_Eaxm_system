# -*- coding: utf-8 -*-
"""交卷后写入考试服务记录。"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.exam import ExamAttempt, ExamPaper, ExamSession
from app.models.exam_service_record import ExamServiceRecord
from app.models.student import Student
from app.models.user import User


def upsert_exam_service_record(
    db: Session,
    att: ExamAttempt,
    sess: ExamSession,
    paper: ExamPaper,
    total_score: Decimal,
) -> None:
    """考生交卷、自动评分后生成或更新一条考试服务记录。"""
    pass_line = paper.pass_score if paper.pass_score is not None else Decimal("0")
    passed = total_score >= pass_line

    u = db.get(User, att.user_id)
    student_display = ""
    if u is not None:
        if u.student_id:
            st = db.get(Student, u.student_id)
            if st is not None:
                student_display = f"{st.student_no or ''} {st.full_name or ''}".strip()
        if not student_display:
            student_display = (u.full_name or u.username or "").strip()

    course_name = "—"
    c = None
    if sess.course_id:
        c = db.get(Course, sess.course_id)
    if c is None and paper.course_id:
        c = db.get(Course, paper.course_id)
    if c is not None and c.name:
        course_name = c.name

    ent = db.get(Enterprise, sess.enterprise_id)
    enterprise_name = ent.name if ent is not None and ent.name else "—"

    row = db.scalars(select(ExamServiceRecord).where(ExamServiceRecord.attempt_id == att.id)).first()
    if row is not None:
        row.enterprise_id = sess.enterprise_id
        row.exam_no = sess.session_code
        row.course_name = course_name
        row.paper_title = paper.title or ""
        row.enterprise_name = enterprise_name
        row.student_display = student_display
        row.score = total_score
        row.passed = passed
        return

    db.add(
        ExamServiceRecord(
            attempt_id=att.id,
            enterprise_id=sess.enterprise_id,
            exam_no=sess.session_code,
            course_name=course_name,
            paper_title=paper.title or "",
            enterprise_name=enterprise_name,
            student_display=student_display,
            score=total_score,
            passed=passed,
        )
    )
