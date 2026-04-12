# -*- coding: utf-8 -*-
"""课程信息 CRUD。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_permission
from app.core.permissions import is_super_role
from app.models.course import Course
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.course import CourseCreate, CourseOut, CourseUpdate
from app.services.data_scope import ensure_same_enterprise

router = APIRouter()


@router.get("", response_model=PageResult[CourseOut])
def list_courses(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.course"))],
    page: Annotated[PageParams, Depends()],
) -> PageResult[CourseOut]:
    """课程列表：超管全部；其余用户仅本企业。"""
    if is_super_role(current):
        stmt = select(func.count()).select_from(Course)
        total = db.scalar(stmt) or 0
        rows = db.scalars(
            select(Course)
            .options(joinedload(Course.enterprise))
            .offset(page.skip)
            .limit(page.limit)
            .order_by(Course.id.desc())
        ).all()
    else:
        if current.enterprise_id is None:
            return PageResult[CourseOut](total=0, items=[])
        stmt = select(func.count()).select_from(Course).where(Course.enterprise_id == current.enterprise_id)
        total = db.scalar(stmt) or 0
        rows = db.scalars(
            select(Course)
            .options(joinedload(Course.enterprise))
            .where(Course.enterprise_id == current.enterprise_id)
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
