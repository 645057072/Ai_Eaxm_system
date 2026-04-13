# -*- coding: utf-8 -*-
"""课程信息 CRUD。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.permissions import is_super_role
from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.course import CourseCreate, CourseOut, CourseUpdate
from app.services.data_scope import ensure_same_enterprise

router = APIRouter()


@router.get("", response_model=PageResult[CourseOut])
def list_courses(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User,
        Depends(require_any_permission("list.course", "list.question")),
    ],
    page: Annotated[PageParams, Depends()],
    keyword: Annotated[str | None, Query(description="模糊匹配课程名称、讲师、所属企业")] = None,
    enterprise_id: Annotated[int | None, Query(description="仅返回该企业下的课程（题库等场景）")] = None,
) -> PageResult[CourseOut]:
    """课程列表：超管全部；其余用户仅本企业。支持 keyword 模糊搜索。"""
    if not is_super_role(current) and current.enterprise_id is None:
        return PageResult[CourseOut](total=0, items=[])

    q = (keyword or "").strip()
    kw_like = f"%{q}%" if q else None

    conds: list = []
    if not is_super_role(current):
        conds.append(Course.enterprise_id == current.enterprise_id)
    elif enterprise_id is not None:
        conds.append(Course.enterprise_id == enterprise_id)
    if kw_like is not None:
        conds.append(
            or_(
                Course.name.like(kw_like),
                Course.instructor.like(kw_like),
                Enterprise.name.like(kw_like),
            )
        )

    base = select(Course).join(Enterprise, Course.enterprise_id == Enterprise.id)
    cnt = select(func.count()).select_from(Course).join(Enterprise, Course.enterprise_id == Enterprise.id)
    if conds:
        w = and_(*conds)
        base = base.where(w)
        cnt = cnt.where(w)

    total = db.scalar(cnt) or 0
    rows = db.scalars(
        base.options(joinedload(Course.enterprise))
        .offset(page.skip)
        .limit(page.limit)
        .order_by(Course.id.desc())
    ).all()
    return PageResult[CourseOut](total=int(total), items=[CourseOut.model_validate(r) for r in rows])


@router.post("", response_model=CourseOut)
def create_course(
    body: CourseCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.course.create"))],
) -> CourseOut:
    """新建课程。"""
    if is_super_role(current):
        if body.enterprise_id is None:
            raise HTTPException(status_code=400, detail="请指定所属企业")
        eid = body.enterprise_id
    else:
        if current.enterprise_id is None:
            raise HTTPException(status_code=400, detail="当前账号未关联企业")
        eid = current.enterprise_id
    c = Course(
        name=body.name,
        instructor=body.instructor,
        period_text=body.period_text,
        description=body.description,
        enterprise_id=eid,
        created_by=current.id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    c = db.scalars(select(Course).options(joinedload(Course.enterprise)).where(Course.id == c.id)).first()
    return CourseOut.model_validate(c)


@router.get("/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.course"))],
) -> CourseOut:
    c = db.scalars(select(Course).options(joinedload(Course.enterprise)).where(Course.id == course_id)).first()
    if c is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if not is_super_role(current):
        ensure_same_enterprise(current, c.enterprise_id)
    return CourseOut.model_validate(c)


@router.patch("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    body: CourseUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.course.update"))],
) -> CourseOut:
    c = db.get(Course, course_id)
    if c is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if not is_super_role(current):
        ensure_same_enterprise(current, c.enterprise_id)
    if body.name is not None:
        c.name = body.name
    if body.instructor is not None:
        c.instructor = body.instructor
    if body.period_text is not None:
        c.period_text = body.period_text
    if body.description is not None:
        c.description = body.description
    db.commit()
    db.refresh(c)
    c = db.scalars(select(Course).options(joinedload(Course.enterprise)).where(Course.id == course_id)).first()
    return CourseOut.model_validate(c)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.course.delete"))],
) -> None:
    c = db.get(Course, course_id)
    if c is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if not is_super_role(current):
        ensure_same_enterprise(current, c.enterprise_id)
    db.delete(c)
    db.commit()
