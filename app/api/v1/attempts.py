# -*- coding: utf-8 -*-
"""保存答案、交卷阅卷。"""

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_permission
from app.core.permissions import has_permission
from app.models.exam import ExamAnswer, ExamAttempt, ExamPaper, ExamPaperItem, ExamSession
from app.models.question import Question
from app.models.user import User
from app.schemas.attempt import AnswersBatchIn, ExamAttemptOut
from app.services.data_scope import ensure_in_managed_enterprise_scope
from app.services.grading import answer_provided, score_for_question
from app.services.exam_candidate_sync import update_exam_candidate_after_submit
from app.services.exam_service_record_sync import upsert_exam_service_record
from app.services.wrong_question_sync import remove_wrong_question, upsert_wrong_question
from app.services.practice_report import build_practice_report, q_type_label_cn

router = APIRouter(prefix="/attempts", tags=["考试作答"])


def _assert_practice_session(db: Session, att: ExamAttempt) -> ExamSession:
    sess = db.get(ExamSession, att.session_id)
    if sess is None:
        raise HTTPException(status_code=400, detail="场次不存在")
    paper = db.get(ExamPaper, sess.paper_id)
    if paper is None:
        raise HTTPException(status_code=400, detail="试卷不存在")
    if (paper.paper_type or "") != "practice":
        raise HTTPException(status_code=400, detail="仅练习卷支持该操作")
    return sess


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dt_as_utc(dt: datetime) -> datetime:
    """与数据库存储混用 naive/aware 时统一为 UTC，避免比较报错500。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.get("/{attempt_id}", response_model=ExamAttemptOut)
def get_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ExamAttemptOut:
    """查询作答记录：本人需 action.exam.take；查看他人需 list.attempt 且同企业。"""
    att = db.scalars(
        select(ExamAttempt)
        .options(joinedload(ExamAttempt.answers))
        .where(ExamAttempt.id == attempt_id)
    ).first()
    if att is None:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    if att.user_id == current.id:
        if not has_permission(db, current, "action.exam.take"):
            raise HTTPException(status_code=403, detail="无权查看")
        return ExamAttemptOut.model_validate(att)
    if not has_permission(db, current, "list.attempt"):
        raise HTTPException(status_code=403, detail="无权查看他人答卷")
    owner = db.get(User, att.user_id)
    if owner is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    ensure_in_managed_enterprise_scope(db, current, owner.enterprise_id)
    return ExamAttemptOut.model_validate(att)


@router.put("/{attempt_id}/answers", response_model=ExamAttemptOut)
def save_answers(
    attempt_id: int,
    body: AnswersBatchIn,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission("action.exam.take")),
) -> ExamAttemptOut:
    """批量保存答案（覆盖同题）。"""
    att = db.get(ExamAttempt, attempt_id)
    if att is None:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    if att.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if att.status != "in_progress":
        raise HTTPException(status_code=400, detail="已交卷，不能修改")
    sess = db.get(ExamSession, att.session_id)
    if sess is None:
        raise HTTPException(status_code=400, detail="场次不存在")
    now = _now()
    if sess.end_at and now > _dt_as_utc(sess.end_at):
        raise HTTPException(status_code=400, detail="考试已结束")

    for row in body.answers:
        ea = db.scalars(
            select(ExamAnswer).where(
                ExamAnswer.attempt_id == attempt_id,
                ExamAnswer.question_id == row.question_id,
            )
        ).first()
        if ea:
            ea.user_answer_json = row.user_answer_json
        else:
            db.add(
                ExamAnswer(
                    attempt_id=attempt_id,
                    question_id=row.question_id,
                    user_answer_json=row.user_answer_json,
                )
            )
    db.commit()
    att2 = db.scalars(
        select(ExamAttempt).options(joinedload(ExamAttempt.answers)).where(ExamAttempt.id == attempt_id)
    ).first()
    return ExamAttemptOut.model_validate(att2)


@router.post("/{attempt_id}/stage", response_model=ExamAttemptOut)
def stage_answers(
    attempt_id: int,
    body: AnswersBatchIn,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission("action.exam.take")),
) -> ExamAttemptOut:
    """练习卷暂存：保存答案并标记 staged，下次进入可提示继续作答。"""
    att = db.get(ExamAttempt, attempt_id)
    if att is None:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    if att.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if att.status != "in_progress":
        raise HTTPException(status_code=400, detail="已交卷，不能暂存")
    sess = _assert_practice_session(db, att)
    now = _now()
    if sess.end_at and now > _dt_as_utc(sess.end_at):
        raise HTTPException(status_code=400, detail="考试已结束")

    for row in body.answers:
        ea = db.scalars(
            select(ExamAnswer).where(
                ExamAnswer.attempt_id == attempt_id,
                ExamAnswer.question_id == row.question_id,
            )
        ).first()
        if ea:
            ea.user_answer_json = row.user_answer_json
        else:
            db.add(
                ExamAnswer(
                    attempt_id=attempt_id,
                    question_id=row.question_id,
                    user_answer_json=row.user_answer_json,
                )
            )
    att.staged = True
    db.commit()
    att2 = db.scalars(
        select(ExamAttempt).options(joinedload(ExamAttempt.answers)).where(ExamAttempt.id == attempt_id)
    ).first()
    return ExamAttemptOut.model_validate(att2)


@router.post("/{attempt_id}/restart-practice", response_model=ExamAttemptOut)
def restart_practice_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission("action.exam.take")),
) -> ExamAttemptOut:
    """练习卷放弃暂存：清空已保存答案，重新开始作答。"""
    att = db.get(ExamAttempt, attempt_id)
    if att is None:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    if att.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if att.status != "in_progress":
        raise HTTPException(status_code=400, detail="已交卷，无法重新开始")
    _assert_practice_session(db, att)
    db.execute(delete(ExamAnswer).where(ExamAnswer.attempt_id == attempt_id))
    att.staged = False
    # 练习卷重新开始作答时，考试时长从当前时刻重新起算
    att.exam_timer_started_at = _now()
    db.commit()
    att2 = db.scalars(
        select(ExamAttempt).options(joinedload(ExamAttempt.answers)).where(ExamAttempt.id == attempt_id)
    ).first()
    return ExamAttemptOut.model_validate(att2)


@router.post("/{attempt_id}/submit", response_model=ExamAttemptOut)
def submit_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission("action.exam.take")),
) -> ExamAttemptOut:
    """交卷并客观题自动阅卷。"""
    att = db.scalars(
        select(ExamAttempt)
        .options(
            joinedload(ExamAttempt.session).joinedload(ExamSession.paper),
        )
        .where(ExamAttempt.id == attempt_id)
    ).first()
    if att is None:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    if att.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if att.status != "in_progress":
        raise HTTPException(status_code=400, detail="已交卷")

    sess = att.session
    if sess is None or sess.paper is None:
        raise HTTPException(status_code=400, detail="场次或试卷数据异常")

    paper = sess.paper
    now = _now()
    if sess.end_at and now > _dt_as_utc(sess.end_at):
        raise HTTPException(status_code=400, detail="考试已结束")
    items = db.scalars(
        select(ExamPaperItem)
        .options(joinedload(ExamPaperItem.question))
        .where(ExamPaperItem.paper_id == paper.id)
    ).all()
    items = sorted(items, key=lambda x: (x.sort_order, x.id))

    total = Decimal("0")
    detail_rows: list[dict] = []
    idx = 0
    for it in items:
        q = it.question
        if q is None:
            continue
        idx += 1
        ea = db.scalars(
            select(ExamAnswer).where(
                ExamAnswer.attempt_id == attempt_id,
                ExamAnswer.question_id == it.question_id,
            )
        ).first()
        ua = ea.user_answer_json if ea else None
        sc = score_for_question(q, ua, it.score)
        total += sc
        if ea:
            ea.score_awarded = sc
        else:
            db.add(
                ExamAnswer(
                    attempt_id=attempt_id,
                    question_id=it.question_id,
                    user_answer_json=ua,
                    score_awarded=sc,
                )
            )
        full_correct = it.score > 0 and sc >= it.score
        answered = answer_provided(q, ua)
        stem_text = (q.stem or "").replace("\n", " ").strip()
        know = (q.analysis or "").strip()
        # 错题集：未作答 或 未得满分 => 入库；已作答且得满分 => 移除
        cid = q.course_id or sess.course_id or paper.course_id
        if cid is not None:
            if (not answered) or (not full_correct):
                upsert_wrong_question(
                    db,
                    enterprise_id=sess.enterprise_id,
                    user_id=att.user_id,
                    course_id=int(cid),
                    question_id=int(q.id),
                )
            else:
                remove_wrong_question(
                    db,
                    enterprise_id=sess.enterprise_id,
                    user_id=att.user_id,
                    course_id=int(cid),
                    question_id=int(q.id),
                )
        detail_rows.append(
            {
                "index": idx,
                "type_label": q_type_label_cn(q.q_type),
                "stem": stem_text,
                "full_correct": full_correct,
                "answered": answered,
                "knowledge": know,
            }
        )

    att.status = "submitted"
    att.submitted_at = _now()
    att.total_score = total
    att.staged = False
    att.practice_report = None
    if (paper.paper_type or "") == "practice":
        full_marks = sum((it.score for it in items if it.question is not None), Decimal("0"))
        att.practice_report = build_practice_report(
            sess.title,
            paper.title,
            total,
            full_marks if full_marks > 0 else Decimal("1"),
            detail_rows,
        )
    update_exam_candidate_after_submit(db, att)
    upsert_exam_service_record(db, att, sess, paper, total)
    db.commit()

    att2 = db.scalars(
        select(ExamAttempt).options(joinedload(ExamAttempt.answers)).where(ExamAttempt.id == attempt_id)
    ).first()
    return ExamAttemptOut.model_validate(att2)
