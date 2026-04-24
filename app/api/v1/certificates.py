# -*- coding: utf-8 -*-
"""证书模板与颁发记录。"""

import secrets
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.permissions import is_super_role
from app.models.certificate import CertRecord, CertTemplate
from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.exam import ExamAttempt
from app.models.exam_service_record import ExamServiceRecord
from app.models.user import User
from app.schemas.certificate import (
    CertRecordIssueBody,
    CertRecordOut,
    CertTemplateCreate,
    CertTemplateOut,
    CertTemplateUpdate,
)
from app.schemas.common import PageParams, PageResult
from app.services.data_scope import ensure_in_managed_enterprise_scope, get_managed_enterprise_ids

router = APIRouter()


def default_cert_layout() -> dict[str, Any]:
    """默认证书版式（占位符与打印模板风格一致，便于后续接 PDF）。"""
    return {
        "paper": {"format": "A4", "widthMm": 210, "heightMm": 297, "portrait": True},
        "title": "结业证书",
        "subtitleTemplate": "{{course_name}}",
        "bodyTemplate": "兹证明 {{student_name}} 参加《{{paper_title}}》考试，成绩 {{score}} 分。",
        "footerTemplate": "证书编号：{{certificate_no}}",
        "signText": "发证单位（签章）",
    }


def _write_enterprise_id(db: Session, current: User, body_enterprise_id: int | None) -> int:
    if is_super_role(current):
        eid = body_enterprise_id
        if eid is None:
            raise HTTPException(status_code=400, detail="请指定所属企业 enterprise_id")
        if db.get(Enterprise, eid) is None:
            raise HTTPException(status_code=404, detail="企业不存在")
        return eid
    if current.enterprise_id is None:
        raise HTTPException(status_code=403, detail="账号未关联企业")
    if body_enterprise_id is not None and body_enterprise_id != current.enterprise_id:
        raise HTTPException(status_code=403, detail="无权指定其他企业")
    return current.enterprise_id


def _assert_course_in_enterprise(db: Session, enterprise_id: int, course_id: int | None) -> None:
    if course_id is None:
        return
    c = db.get(Course, course_id)
    if c is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if c.enterprise_id != enterprise_id:
        raise HTTPException(status_code=400, detail="课程不属于该证书模板所属企业")


def _load_template(db: Session, tid: int) -> CertTemplate | None:
    return db.scalars(
        select(CertTemplate)
        .options(joinedload(CertTemplate.enterprise), joinedload(CertTemplate.course))
        .where(CertTemplate.id == tid)
    ).first()


def assert_template_manageable(db: Session, current: User, tid: int) -> CertTemplate:
    t = _load_template(db, tid)
    if t is None:
        raise HTTPException(status_code=404, detail="证书模板不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, t.enterprise_id)
    return t


def _template_to_out(t: CertTemplate) -> CertTemplateOut:
    return CertTemplateOut(
        id=t.id,
        enterprise_id=t.enterprise_id,
        enterprise_name=t.enterprise.name if t.enterprise else None,
        cert_code=t.cert_code,
        name=t.name,
        course_id=t.course_id,
        course_name=t.course.name if t.course else None,
        layout_json=t.layout_json or {},
        status=t.status,
        created_by=t.created_by,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _record_to_out(r: CertRecord) -> CertRecordOut:
    tpl = r.template
    u = r.user
    iss = r.issuer
    svc = r.service_record
    return CertRecordOut(
        id=r.id,
        enterprise_id=r.enterprise_id,
        certificate_no=r.certificate_no,
        cert_template_id=r.cert_template_id,
        template_name=tpl.name if tpl else None,
        cert_code=tpl.cert_code if tpl else None,
        user_id=r.user_id,
        user_username=u.username if u else None,
        exam_service_record_id=r.exam_service_record_id,
        exam_no=svc.exam_no if svc else None,
        student_display=r.student_display,
        course_name=r.course_name,
        paper_title=r.paper_title,
        score=r.score,
        passed=r.passed,
        issued_at=r.issued_at,
        issued_by=r.issued_by,
        issuer_name=(iss.full_name or iss.username) if iss else None,
    )


@router.get("/templates", response_model=PageResult[CertTemplateOut])
def list_cert_templates(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_any_permission("menu.exam.certificate", "list.cert_template"))],
    page: Annotated[PageParams, Depends()],
    keyword: str | None = Query(default=None, description="编码/名称模糊"),
    enterprise_id: int | None = Query(default=None, ge=1),
) -> PageResult[CertTemplateOut]:
    q = select(CertTemplate).options(joinedload(CertTemplate.enterprise), joinedload(CertTemplate.course))
    cnt = select(func.count()).select_from(CertTemplate)
    if not is_super_role(current):
        managed = get_managed_enterprise_ids(db, current)
        if not managed:
            return PageResult[CertTemplateOut](total=0, items=[])
        q = q.where(CertTemplate.enterprise_id.in_(managed))
        cnt = cnt.where(CertTemplate.enterprise_id.in_(managed))
    elif enterprise_id is not None:
        q = q.where(CertTemplate.enterprise_id == enterprise_id)
        cnt = cnt.where(CertTemplate.enterprise_id == enterprise_id)
    kw = (keyword or "").strip()
    if kw:
        like = f"%{kw}%"
        q = q.where(or_(CertTemplate.cert_code.like(like), CertTemplate.name.like(like)))
        cnt = cnt.where(or_(CertTemplate.cert_code.like(like), CertTemplate.name.like(like)))
    total = db.scalar(cnt) or 0
    rows = db.scalars(q.order_by(CertTemplate.id.desc()).offset(page.skip).limit(page.limit)).all()
    return PageResult[CertTemplateOut](total=int(total), items=[_template_to_out(t) for t in rows])


@router.post("/templates", response_model=CertTemplateOut)
def create_cert_template(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.cert_template.manage"))],
    body: CertTemplateCreate,
) -> CertTemplateOut:
    eid = _write_enterprise_id(db, current, body.enterprise_id)
    code = body.cert_code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="模板编码不能为空")
    exists = db.scalars(
        select(CertTemplate).where(
            CertTemplate.enterprise_id == eid,
            CertTemplate.cert_code == code,
        )
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="该企业下模板编码已存在")
    _assert_course_in_enterprise(db, eid, body.course_id)
    layout = body.layout_json if body.layout_json is not None else default_cert_layout()
    st = (body.status or "draft").lower()
    if st not in ("draft", "published"):
        raise HTTPException(status_code=400, detail="status 仅支持 draft / published")
    t = CertTemplate(
        enterprise_id=eid,
        cert_code=code,
        name=(body.name or "").strip(),
        course_id=body.course_id,
        layout_json=layout,
        status=st,
        created_by=current.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    t = _load_template(db, t.id)
    assert t is not None
    return _template_to_out(t)


@router.get("/templates/{template_id}", response_model=CertTemplateOut)
def get_cert_template(
    template_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_any_permission("menu.exam.certificate", "list.cert_template"))],
) -> CertTemplateOut:
    t = assert_template_manageable(db, current, template_id)
    return _template_to_out(t)


@router.patch("/templates/{template_id}", response_model=CertTemplateOut)
def update_cert_template(
    template_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.cert_template.manage"))],
    body: CertTemplateUpdate,
) -> CertTemplateOut:
    t = assert_template_manageable(db, current, template_id)
    if body.name is not None:
        t.name = body.name.strip()
    if body.course_id is not None:
        _assert_course_in_enterprise(db, t.enterprise_id, body.course_id)
        t.course_id = body.course_id
    if body.layout_json is not None:
        t.layout_json = body.layout_json
    if body.status is not None:
        st = body.status.lower()
        if st not in ("draft", "published"):
            raise HTTPException(status_code=400, detail="status 仅支持 draft / published")
        t.status = st
    db.commit()
    db.refresh(t)
    t2 = _load_template(db, template_id)
    assert t2 is not None
    return _template_to_out(t2)


@router.delete("/templates/{template_id}")
def delete_cert_template(
    template_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.cert_template.manage"))],
) -> dict:
    t = assert_template_manageable(db, current, template_id)
    n = (
        db.scalar(
            select(func.count()).select_from(CertRecord).where(CertRecord.cert_template_id == template_id)
        )
        or 0
    )
    if int(n) > 0:
        raise HTTPException(status_code=400, detail="已有颁发记录引用该模板，无法删除")
    db.delete(t)
    db.commit()
    return {"ok": True}


@router.get("/records", response_model=PageResult[CertRecordOut])
def list_cert_records(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_any_permission("menu.exam.certificate", "list.cert_record"))],
    page: Annotated[PageParams, Depends()],
    keyword: str | None = Query(default=None, description="证书编号/学员/课程/试卷/模板编码"),
) -> PageResult[CertRecordOut]:
    conds: list = []
    if not is_super_role(current):
        managed = get_managed_enterprise_ids(db, current)
        if not managed:
            return PageResult[CertRecordOut](total=0, items=[])
        conds.append(CertRecord.enterprise_id.in_(managed))
    kw = (keyword or "").strip()
    if kw:
        like = f"%{kw}%"
        conds.append(
            or_(
                CertRecord.certificate_no.like(like),
                CertRecord.student_display.like(like),
                CertRecord.course_name.like(like),
                CertRecord.paper_title.like(like),
                CertTemplate.cert_code.like(like),
                CertTemplate.name.like(like),
            )
        )
    w = and_(*conds) if conds else None

    q = select(CertRecord).options(
        joinedload(CertRecord.template),
        joinedload(CertRecord.user),
        joinedload(CertRecord.issuer),
        joinedload(CertRecord.service_record),
    )
    cnt = select(func.count()).select_from(CertRecord)
    if kw:
        q = q.join(CertTemplate, CertTemplate.id == CertRecord.cert_template_id)
        cnt = cnt.join(CertTemplate, CertTemplate.id == CertRecord.cert_template_id)
    if w is not None:
        q = q.where(w)
        cnt = cnt.where(w)
    total = db.scalar(cnt) or 0
    rows = db.scalars(q.order_by(CertRecord.id.desc()).offset(page.skip).limit(page.limit)).all()
    return PageResult[CertRecordOut](total=int(total), items=[_record_to_out(r) for r in rows])


@router.post("/records/issue", response_model=CertRecordOut)
def issue_cert_record(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.cert_record.issue"))],
    body: CertRecordIssueBody,
) -> CertRecordOut:
    tpl = assert_template_manageable(db, current, body.cert_template_id)
    if tpl.status != "published":
        raise HTTPException(status_code=400, detail="请使用已发布（published）的证书模板")

    rec = db.get(ExamServiceRecord, body.exam_service_record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="考试服务记录不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, rec.enterprise_id)
    if rec.enterprise_id != tpl.enterprise_id:
        raise HTTPException(status_code=400, detail="考试记录与证书模板不属于同一企业")
    if body.require_passed and not rec.passed:
        raise HTTPException(status_code=400, detail="该考试记录未通过，不能颁发证书")

    if tpl.course_id is not None:
        c = db.get(Course, tpl.course_id)
        cname = (c.name if c else "").strip()
        rname = (rec.course_name or "").strip()
        if cname != rname:
            raise HTTPException(status_code=400, detail="该模板限定课程与考试记录课程名称不一致")

    dup = db.scalars(
        select(CertRecord).where(
            CertRecord.exam_service_record_id == rec.id,
            CertRecord.cert_template_id == tpl.id,
        )
    ).first()
    if dup:
        raise HTTPException(status_code=400, detail="该考试记录已使用此模板颁发过证书")

    att = db.get(ExamAttempt, rec.attempt_id)
    if att is None:
        raise HTTPException(status_code=400, detail="作答记录缺失，无法确定获证人")
    uid = att.user_id

    ent_id = tpl.enterprise_id
    for _ in range(5):
        certificate_no = f"C{ent_id}{datetime.now(timezone.utc).strftime('%Y%m%d')}{secrets.token_hex(4).upper()}"
        exists = db.scalars(select(CertRecord).where(CertRecord.certificate_no == certificate_no)).first()
        if not exists:
            break
    else:
        raise HTTPException(status_code=500, detail="生成证书编号失败，请重试")

    row = CertRecord(
        enterprise_id=ent_id,
        cert_template_id=tpl.id,
        user_id=uid,
        exam_service_record_id=rec.id,
        certificate_no=certificate_no,
        student_display=rec.student_display or "",
        course_name=rec.course_name or "",
        paper_title=rec.paper_title or "",
        score=rec.score,
        passed=rec.passed,
        issued_by=current.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    r2 = db.scalars(
        select(CertRecord)
        .options(
            joinedload(CertRecord.template),
            joinedload(CertRecord.user),
            joinedload(CertRecord.issuer),
            joinedload(CertRecord.service_record),
        )
        .where(CertRecord.id == row.id)
    ).first()
    assert r2 is not None
    return _record_to_out(r2)
