# -*- coding: utf-8 -*-
"""学员管理 CRUD + 导入附件上传。"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import and_, false, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.config import get_settings
from app.core.permissions import is_super_role
from app.models.enterprise import Enterprise
from app.models.student import Student
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate
from app.services.data_scope import ensure_same_enterprise

router = APIRouter()

_ALLOWED_IMPORT_EXT = {
    "doc",
    "docx",
    "xls",
    "xlsx",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "webp",
    "csv",
    "txt",
}

_BIRTH_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_birth_month(v: str | None) -> str | None:
    if not v:
        return None
    s = v.strip()
    if not s:
        return None
    if not _BIRTH_MONTH_RE.match(s):
        raise HTTPException(status_code=400, detail="出生年月格式错误，应为 YYYY-MM")
    return s


def _restrict_students_query_by_tenant(q, current: User) -> any:
    if is_super_role(current):
        return q
    if current.enterprise_id is None:
        return q.where(false())
    return q.where(Student.enterprise_id == current.enterprise_id)


@router.get("", response_model=PageResult[StudentOut])
def list_students(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.student"))],
    page: Annotated[PageParams, Depends()],
    student_keyword: str | None = Query(default=None, description="学员编号模糊匹配"),
    name_keyword: str | None = Query(default=None, description="姓名模糊匹配"),
    enterprise_id: int | None = Query(default=None, description="按所属企业筛选（超管可用）"),
) -> PageResult[StudentOut]:
    """学员列表：支持编号/姓名模糊筛选。"""
    conds: list = []
    sn = (student_keyword or "").strip()
    nm = (name_keyword or "").strip()
    if sn:
        conds.append(Student.student_no.like(f"%{sn}%"))
    if nm:
        conds.append(Student.full_name.like(f"%{nm}%"))
    if enterprise_id is not None and is_super_role(current):
        conds.append(Student.enterprise_id == enterprise_id)
    w = and_(*conds) if conds else None

    cnt = select(func.count()).select_from(Student).outerjoin(Enterprise, Student.enterprise_id == Enterprise.id)
    q = select(Student, Enterprise.name).outerjoin(Enterprise, Student.enterprise_id == Enterprise.id)
    q = _restrict_students_query_by_tenant(q, current)
    cnt = _restrict_students_query_by_tenant(cnt, current)
    if w is not None:
        q = q.where(w)
        cnt = cnt.where(w)
    total = db.scalar(cnt) or 0
    rows = db.execute(q.offset(page.skip).limit(page.limit).order_by(Student.id.desc())).all()
    items: list[StudentOut] = []
    for stu, ename in rows:
        out = StudentOut.model_validate(stu)
        out.enterprise_name = ename
        items.append(out)
    return PageResult[StudentOut](total=int(total), items=items)


@router.get("/lookup")
def lookup_students(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User,
        Depends(
            require_any_permission(
                "action.user.create",
                "action.user.update",
                "action.role.permission",
                "list.student",
            )
        ),
    ],
    keyword: str | None = Query(default=None, description="按学员编号/姓名模糊查询"),
    enterprise_id: int | None = Query(default=None, description="按所属企业筛选（超管可用）"),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict:
    """用于用户关联学员：返回精简字段，避免依赖学员列表权限。"""
    kw = (keyword or "").strip()
    if not kw:
        return {"items": []}
    conds: list = [
        (Student.student_no.like(f"%{kw}%")) | (Student.full_name.like(f"%{kw}%")),
    ]
    if enterprise_id is not None and is_super_role(current):
        conds.append(Student.enterprise_id == enterprise_id)
    w = and_(*conds) if conds else None

    q = select(Student).order_by(Student.id.desc()).limit(limit)
    q = _restrict_students_query_by_tenant(q, current)
    if w is not None:
        q = q.where(w)
    rows = db.scalars(q).all()
    return {
        "items": [{"id": r.id, "student_no": r.student_no, "full_name": r.full_name} for r in rows],
    }


@router.post("", response_model=StudentOut)
def create_student(
    body: StudentCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.student.create"))],
) -> StudentOut:
    """新建学员。"""
    ent = body.enterprise_id if is_super_role(current) else current.enterprise_id
    if not is_super_role(current):
        ensure_same_enterprise(current, ent)
    if is_super_role(current) and ent is None:
        # 超管未指定则按自身企业（允许为空）
        ent = current.enterprise_id

    obj = Student(
        student_no=body.student_no.strip(),
        full_name=body.full_name.strip(),
        gender=(body.gender or None),
        birth_month=_normalize_birth_month(body.birth_month),
        phone=(body.phone or None),
        id_card_no=(body.id_card_no or None),
        address_phone=(body.address_phone or None),
        remark=(body.remark or None),
        enterprise_id=ent,
        created_by=current.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return StudentOut.model_validate(obj)


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    body: StudentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.student.update"))],
) -> StudentOut:
    obj = db.get(Student, student_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="学员不存在")
    # 归属校验
    if not is_super_role(current):
        ensure_same_enterprise(current, obj.enterprise_id)
    data = body.model_dump(exclude_unset=True)
    if "birth_month" in data:
        data["birth_month"] = _normalize_birth_month(data.get("birth_month"))
    if "enterprise_id" in data and not is_super_role(current):
        data.pop("enterprise_id", None)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return StudentOut.model_validate(obj)


@router.delete("/{student_id}", status_code=204)
def delete_student(
    student_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.student.delete"))],
) -> None:
    obj = db.get(Student, student_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="学员不存在")
    if not is_super_role(current):
        ensure_same_enterprise(current, obj.enterprise_id)
    db.delete(obj)
    db.commit()


@router.post("/import", response_model=dict)
async def import_students_files(
    current: Annotated[User, Depends(require_permission("action.student.import"))],
    files: Annotated[
        List[UploadFile] | None,
        File(description="可选择多个文件，字段名 files；支持 word/excel/pdf/图片/csv/txt"),
    ] = None,
    file: Annotated[UploadFile | None, File(description="兼容单文件，字段名 file")] = None,
    note: Annotated[str | None, Form(description="导入备注")] = None,
) -> dict:
    """导入信息：先上传存档（后续可扩展解析入库）。"""
    upload_list: List[UploadFile] = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)
    if not upload_list:
        raise HTTPException(status_code=400, detail="请选择文件")

    root = Path(get_settings().upload_root) / "student_import"
    root.mkdir(parents=True, exist_ok=True)
    saved: list[dict] = []
    ts = _now().strftime("%Y%m%d%H%M%S")
    ent = current.enterprise_id or 0

    for idx, uf in enumerate(upload_list):
        fn = (uf.filename or "upload").strip()
        ext = fn.split(".")[-1].lower() if "." in fn else ""
        if ext not in _ALLOWED_IMPORT_EXT:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型：{fn}")
        raw = await uf.read()
        if len(raw) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"单个文件超过 20MB：{fn}")
        safe = f"stu_{ent}_{ts}_{idx}.{ext}"
        path = root / safe
        path.write_bytes(raw)
        saved.append({"name": safe, "orig": fn, "bytes": len(raw)})

    return {"saved": saved, "note": note or "", "count": len(saved)}

