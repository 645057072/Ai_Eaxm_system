# -*- coding: utf-8 -*-
"""考生管理 CRUD。"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import and_, false, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_permission
from app.core.permissions import is_super_role
from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.exam import ExamAttempt, ExamSession
from app.models.exam_candidate import ExamCandidate
from app.models.student import Student
from app.models.user import User
from app.services.attempt_pdf import build_attempt_pdf_bytes
from app.schemas.common import PageParams, PageResult
from app.schemas.exam_candidate import ExamCandidateCreate, ExamCandidateOut, ExamCandidateUpdate
from app.services.data_scope import ensure_in_managed_enterprise_scope, get_managed_enterprise_ids

router = APIRouter()


def _restrict_exam_candidate_query(q, db: Session, current: User):
    if is_super_role(current):
        return q
    managed = get_managed_enterprise_ids(db, current)
    if not managed:
        return q.where(false())
    return q.where(ExamCandidate.enterprise_id.in_(managed))


def _resolve_enterprise_id(db: Session, current: User, body_ent: int | None) -> int:
    if is_super_role(current):
        if body_ent is None:
            raise HTTPException(status_code=400, detail="请指定所属企业")
        ensure_in_managed_enterprise_scope(db, current, body_ent)
        return body_ent
    if current.enterprise_id is None:
        raise HTTPException(status_code=400, detail="当前账号未关联企业")
    if body_ent is not None:
        ensure_in_managed_enterprise_scope(db, current, body_ent)
        return body_ent
    return current.enterprise_id


def _assert_course_student_match_enterprise(
    db: Session, ent_id: int, course_id: int, student_id: int
) -> None:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=400, detail="课程不存在")
    if course.enterprise_id != ent_id:
        raise HTTPException(status_code=400, detail="课程与所属企业不一致")
    stu = db.get(Student, student_id)
    if stu is None:
        raise HTTPException(status_code=400, detail="学员不存在")
    if stu.enterprise_id is None:
        raise HTTPException(status_code=400, detail="学员未关联企业，无法登记")
    if stu.enterprise_id != ent_id:
        raise HTTPException(status_code=400, detail="学员与所属企业不一致")


def _row_to_out(
    ec: ExamCandidate,
    ename: str | None,
    cname: str | None,
    stu_no: str | None,
    stu_name: str | None,
) -> ExamCandidateOut:
    out = ExamCandidateOut.model_validate(ec)
    out.enterprise_name = ename
    out.course_name = cname
    out.student_no = stu_no
    out.student_name = stu_name
    return out


@router.get("/student-choices")
def student_choices(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.exam_candidate"))],
    enterprise_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None, description="学员编号/姓名模糊"),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    """下拉：按企业筛选学员（无需 list.student）。"""
    eid = enterprise_id
    if eid is None:
        if is_super_role(current):
            return {"items": []}
        eid = current.enterprise_id
    if eid is None:
        return {"items": []}
    ensure_in_managed_enterprise_scope(db, current, eid)
    q = select(Student).where(Student.enterprise_id == eid)
    kw = (keyword or "").strip()
    if kw:
        q = q.where((Student.student_no.like(f"%{kw}%")) | (Student.full_name.like(f"%{kw}%")))
    q = q.order_by(Student.id.desc()).limit(limit)
    rows = db.scalars(q).all()
    return {
        "items": [{"id": r.id, "student_no": r.student_no, "full_name": r.full_name} for r in rows],
    }


@router.get("/{candidate_id}/attempt-pdf")
def download_candidate_attempt_pdf(
    candidate_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.exam_candidate"))],
) -> Response:
    """下载该考生最近一次答卷明细 PDF。"""
    obj = db.get(ExamCandidate, candidate_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="考生记录不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, obj.enterprise_id)
    if not obj.last_attempt_id:
        raise HTTPException(status_code=400, detail="暂无作答记录，无法生成 PDF")
    try:
        pdf_bytes = build_attempt_pdf_bytes(db, obj.last_attempt_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    fn = f"exam_attempt_{obj.last_attempt_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )


@router.get("/{candidate_id}/attempt-report")
def get_candidate_attempt_report(
    candidate_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.exam_candidate"))],
) -> dict[str, Any]:
    """考生最近一次作答的评估报告（练习卷含 practice_report）。"""
    obj = db.get(ExamCandidate, candidate_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="考生记录不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, obj.enterprise_id)
    if not obj.last_attempt_id:
        raise HTTPException(status_code=400, detail="暂无作答记录")
    att = db.scalars(
        select(ExamAttempt)
        .options(
            joinedload(ExamAttempt.session).joinedload(ExamSession.paper),
        )
        .where(ExamAttempt.id == obj.last_attempt_id)
    ).first()
    if att is None:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    sess = att.session
    paper = sess.paper if sess else None
    return {
        "attempt_id": att.id,
        "status": att.status,
        "total_score": str(att.total_score) if att.total_score is not None else None,
        "practice_report": att.practice_report,
        "session_title": sess.title if sess else None,
        "paper_title": paper.title if paper else None,
        "paper_type": (paper.paper_type or "formal") if paper else "formal",
    }


@router.get("", response_model=PageResult[ExamCandidateOut])
def list_exam_candidates(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.exam_candidate"))],
    page: Annotated[PageParams, Depends()],
    exam_no_keyword: str | None = Query(default=None, description="考试编号模糊"),
    enterprise_id: int | None = Query(default=None, description="按企业筛选（超管可用）"),
) -> PageResult[ExamCandidateOut]:
    conds: list = []
    kn = (exam_no_keyword or "").strip()
    if kn:
        conds.append(ExamCandidate.exam_no.like(f"%{kn}%"))
    if enterprise_id is not None:
        if is_super_role(current):
            conds.append(ExamCandidate.enterprise_id == enterprise_id)
        else:
            ensure_in_managed_enterprise_scope(db, current, enterprise_id)
            conds.append(ExamCandidate.enterprise_id == enterprise_id)
    w = and_(*conds) if conds else None

    base = (
        select(ExamCandidate, Enterprise.name, Course.name, Student.student_no, Student.full_name)
        .outerjoin(Enterprise, ExamCandidate.enterprise_id == Enterprise.id)
        .outerjoin(Course, ExamCandidate.course_id == Course.id)
        .outerjoin(Student, ExamCandidate.student_id == Student.id)
    )
    cnt = select(func.count()).select_from(ExamCandidate)
    base = _restrict_exam_candidate_query(base, db, current)
    cnt = _restrict_exam_candidate_query(cnt, db, current)
    if w is not None:
        base = base.where(w)
        cnt = cnt.where(w)
    total = db.scalar(cnt) or 0
    rows = db.execute(base.offset(page.skip).limit(page.limit).order_by(ExamCandidate.id.desc())).all()
    items = [_row_to_out(ec, en, cn, sn, fn) for ec, en, cn, sn, fn in rows]
    return PageResult[ExamCandidateOut](total=int(total), items=items)


@router.post("", response_model=ExamCandidateOut)
def create_exam_candidate(
    body: ExamCandidateCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.exam_candidate.create"))],
) -> ExamCandidateOut:
    ent_id = _resolve_enterprise_id(db, current, body.enterprise_id)
    _assert_course_student_match_enterprise(db, ent_id, body.course_id, body.student_id)
    obj = ExamCandidate(
        exam_no=body.exam_no.strip(),
        enterprise_id=ent_id,
        course_id=body.course_id,
        student_id=body.student_id,
    )
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="该企业下相同考试编号与学员已存在")
    db.refresh(obj)
    return _load_out(db, obj.id)


@router.patch("/{candidate_id}", response_model=ExamCandidateOut)
def update_exam_candidate(
    candidate_id: int,
    body: ExamCandidateUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.exam_candidate.update"))],
) -> ExamCandidateOut:
    obj = db.get(ExamCandidate, candidate_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="考生记录不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, obj.enterprise_id)

    data = body.model_dump(exclude_unset=True)
    if "enterprise_id" in data and not is_super_role(current):
        data.pop("enterprise_id", None)

    ent_id = obj.enterprise_id
    if "enterprise_id" in data and data["enterprise_id"] is not None:
        ensure_in_managed_enterprise_scope(db, current, data["enterprise_id"])
        ent_id = data["enterprise_id"]

    course_id = data.get("course_id", obj.course_id)
    student_id = data.get("student_id", obj.student_id)
    if "course_id" in data or "student_id" in data or "enterprise_id" in data:
        _assert_course_student_match_enterprise(db, ent_id, int(course_id), int(student_id))

    for k, v in data.items():
        if k == "exam_no" and isinstance(v, str):
            setattr(obj, k, v.strip())
        else:
            setattr(obj, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="该企业下相同考试编号与学员已存在")
    db.refresh(obj)
    return _load_out(db, obj.id)


@router.delete("/{candidate_id}", status_code=204)
def delete_exam_candidate(
    candidate_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.exam_candidate.delete"))],
) -> None:
    obj = db.get(ExamCandidate, candidate_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="考生记录不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, obj.enterprise_id)
    db.delete(obj)
    db.commit()


def _load_out(db: Session, pk: int) -> ExamCandidateOut:
    row = db.execute(
        select(ExamCandidate, Enterprise.name, Course.name, Student.student_no, Student.full_name)
        .outerjoin(Enterprise, ExamCandidate.enterprise_id == Enterprise.id)
        .outerjoin(Course, ExamCandidate.course_id == Course.id)
        .outerjoin(Student, ExamCandidate.student_id == Student.id)
        .where(ExamCandidate.id == pk)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="考生记录不存在")
    ec, en, cn, sn, fn = row
    return _row_to_out(ec, en, cn, sn, fn)
