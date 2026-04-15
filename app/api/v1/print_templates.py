# -*- coding: utf-8 -*-
"""打印模板：列表、表单、发布与版式保存。"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.permissions import is_super_role
from app.models.course import Course
from app.models.print_template import PrintTemplate
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.print_template import (
    PrintTemplateCreate,
    PrintTemplateOut,
    PrintTemplatePublishBody,
    PrintTemplateUpdate,
)
from app.services.data_scope import ensure_in_managed_enterprise_scope, get_managed_enterprise_ids

router = APIRouter()

_PAPER_MM: dict[str, tuple[int, int]] = {
    "A4": (210, 297),
    "A3": (297, 420),
    "B5": (176, 250),
    "CUSTOM": (210, 297),
}


def default_layout_json(paper_format: str) -> dict[str, Any]:
    """按纸张规格生成默认版式（供重置与设计中心初始值）。"""
    fmt = (paper_format or "A4").upper()
    w, h = _PAPER_MM.get(fmt, _PAPER_MM["A4"])
    return {
        "paper": {"format": fmt, "widthMm": w, "heightMm": h, "portrait": True},
        "marginMm": {"top": 15, "right": 15, "bottom": 15, "left": 15},
        "header": {
            "show": True,
            "titleTemplate": "{{paper_title}}",
            "fontPt": 14,
            "align": "center",
        },
        "question": {"fontPt": 11, "lineHeight": 1.6},
        "footer": {"show": True, "textTemplate": "第 {{page}}页 / 共 {{pages}} 页", "fontPt": 9},
    }


def _assert_course_manageable(db: Session, current: User, course_id: int) -> Course:
    c = db.get(Course, course_id)
    if c is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, c.enterprise_id)
    return c


def _template_to_out(t: PrintTemplate) -> PrintTemplateOut:
    return PrintTemplateOut(
        id=t.id,
        template_no=t.template_no,
        template_name=t.template_name,
        module_code=t.module_code,
        menu_code=t.menu_code,
        course_id=t.course_id,
        course_name=t.course.name if t.course else None,
        paper_format=t.paper_format,
        layout_json=t.layout_json or {},
        publish_scope_enterprise_id=t.publish_scope_enterprise_id,
        publish_scope_enterprise_name=t.publish_scope_enterprise.name
        if t.publish_scope_enterprise
        else None,
        status=t.status,
        created_by=t.created_by,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _load_template(db: Session, tid: int) -> PrintTemplate | None:
    return db.scalars(
        select(PrintTemplate)
        .options(
            joinedload(PrintTemplate.course),
            joinedload(PrintTemplate.publish_scope_enterprise),
        )
        .where(PrintTemplate.id == tid)
    ).first()


def assert_template_manageable(db: Session, current: User, tid: int) -> PrintTemplate:
    t = _load_template(db, tid)
    if t is None:
        raise HTTPException(status_code=404, detail="打印模板不存在")
    _assert_course_manageable(db, current, t.course_id)
    return t


@router.get("", response_model=PageResult[PrintTemplateOut])
def list_print_templates(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_any_permission("menu.system.print", "list.print_template"))],
    page: Annotated[PageParams, Depends()],
    course_id: int | None = Query(default=None, ge=1),
    status: str | None = None,
) -> PageResult[PrintTemplateOut]:
    q = select(PrintTemplate).options(joinedload(PrintTemplate.course), joinedload(PrintTemplate.publish_scope_enterprise))
    cnt = select(func.count()).select_from(PrintTemplate)
    if not is_super_role(current):
        managed = get_managed_enterprise_ids(db, current)
        if not managed:
            return PageResult[PrintTemplateOut](total=0, items=[])
        q = q.join(Course, PrintTemplate.course_id == Course.id).where(Course.enterprise_id.in_(managed))
        cnt = cnt.join(Course, PrintTemplate.course_id == Course.id).where(Course.enterprise_id.in_(managed))
    if course_id is not None:
        _assert_course_manageable(db, current, course_id)
        q = q.where(PrintTemplate.course_id == course_id)
        cnt = cnt.where(PrintTemplate.course_id == course_id)
    if status:
        q = q.where(PrintTemplate.status == status)
        cnt = cnt.where(PrintTemplate.status == status)
    total = db.scalar(cnt) or 0
    rows = db.scalars(
        q.order_by(PrintTemplate.id.desc()).offset(page.skip).limit(page.limit)
    ).all()
    return PageResult[PrintTemplateOut](total=int(total), items=[_template_to_out(r) for r in rows])


@router.get("/resolve", response_model=PrintTemplateOut | None)
def resolve_template_for_course(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User,
        Depends(require_any_permission("menu.system.print", "list.print_template", "action.paper.manage")),
    ],
    course_id: Annotated[int, Query(ge=1)],
) -> PrintTemplateOut | None:
    """供后期试卷打印选用：返回该课程已发布且当前用户可用的模板（优先本企业限定，其次全局）。"""
    _assert_course_manageable(db, current, course_id)
    base = (
        select(PrintTemplate)
        .options(joinedload(PrintTemplate.course), joinedload(PrintTemplate.publish_scope_enterprise))
        .where(PrintTemplate.course_id == course_id, PrintTemplate.status == "published")
        .order_by(PrintTemplate.id.desc())
    )
    rows = db.scalars(base).all()
    if not rows:
        return None
    if is_super_role(current):
        return _template_to_out(rows[0])
    eid = current.enterprise_id
    for t in rows:
        if t.publish_scope_enterprise_id is None:
            return _template_to_out(t)
        if eid is not None and t.publish_scope_enterprise_id == eid:
            return _template_to_out(t)
    return None


@router.get("/{template_id}", response_model=PrintTemplateOut)
def get_print_template(
    template_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_any_permission("menu.system.print", "list.print_template"))],
) -> PrintTemplateOut:
    t = assert_template_manageable(db, current, template_id)
    return _template_to_out(t)


@router.post("", response_model=PrintTemplateOut)
def create_print_template(
    body: PrintTemplateCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.print_template.manage"))],
) -> PrintTemplateOut:
    _assert_course_manageable(db, current, body.course_id)
    if db.scalar(select(func.count()).select_from(PrintTemplate).where(PrintTemplate.template_no == body.template_no)):
        raise HTTPException(status_code=400, detail="模板编号已存在")
    fmt = (body.paper_format or "A4").upper()
    t = PrintTemplate(
        template_no=body.template_no.strip(),
        template_name=(body.template_name or "").strip(),
        module_code=body.module_code.strip(),
        menu_code=body.menu_code.strip(),
        course_id=body.course_id,
        paper_format=fmt,
        layout_json=default_layout_json(fmt),
        status="draft",
        created_by=current.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    t2 = _load_template(db, t.id)
    assert t2 is not None
    return _template_to_out(t2)


@router.patch("/{template_id}", response_model=PrintTemplateOut)
def update_print_template(
    template_id: int,
    body: PrintTemplateUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.print_template.manage"))],
) -> PrintTemplateOut:
    t = assert_template_manageable(db, current, template_id)
    data = body.model_dump(exclude_unset=True)
    if "course_id" in data and data["course_id"] is not None:
        _assert_course_manageable(db, current, data["course_id"])
    if "paper_format" in data and data["paper_format"] is not None:
        data["paper_format"] = str(data["paper_format"]).upper()
    for k, v in data.items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    t2 = _load_template(db, template_id)
    assert t2 is not None
    return _template_to_out(t2)


@router.post("/{template_id}/reset", response_model=PrintTemplateOut)
def reset_print_template(
    template_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.print_template.manage"))],
) -> PrintTemplateOut:
    """重置为当前纸张规格下的默认版式。"""
    t = assert_template_manageable(db, current, template_id)
    t.layout_json = default_layout_json(t.paper_format)
    db.commit()
    db.refresh(t)
    t2 = _load_template(db, template_id)
    assert t2 is not None
    return _template_to_out(t2)


@router.post("/{template_id}/publish", response_model=PrintTemplateOut)
def publish_print_template(
    template_id: int,
    body: PrintTemplatePublishBody,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.print_template.manage"))],
) -> PrintTemplateOut:
    t = assert_template_manageable(db, current, template_id)
    scope_id = body.enterprise_id
    if scope_id is not None:
        ensure_in_managed_enterprise_scope(db, current, scope_id)
    t.status = "published"
    t.publish_scope_enterprise_id = scope_id
    db.commit()
    db.refresh(t)
    t2 = _load_template(db, template_id)
    assert t2 is not None
    return _template_to_out(t2)


@router.delete("/{template_id}", status_code=204)
def delete_print_template(
    template_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.print_template.manage"))],
) -> None:
    t = assert_template_manageable(db, current, template_id)
    db.delete(t)
    db.commit()
