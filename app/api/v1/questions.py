# -*- coding: utf-8 -*-

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

from app.api.deps import get_db, require_any_permission, require_permission
from app.core.permissions import is_super_role
from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.question import Question
from app.models.user import User
from app.schemas.common import PageParams, PageResult
from app.schemas.question import (
    QuestionBatchPublishIn,
    QuestionCreate,
    QuestionImportResult,
    QuestionOut,
    QuestionUpdate,
)
from app.services.data_scope import assert_question_in_enterprise, restrict_query_by_creator_enterprise
from app.services.question_number import allocate_question_no
from app.services.question_import import (
    build_image_placeholder,
    build_questions_from_text,
    extract_plain_text,
    normalize_analysis,
)

router = APIRouter()


def _to_out(obj: Question) -> QuestionOut:
    return QuestionOut(
        id=obj.id,
        question_no=obj.question_no,
        q_type=obj.q_type,
        stem=obj.stem,
        options_json=obj.options_json,
        answer_json=obj.answer_json,
        analysis=obj.analysis,
        difficulty=obj.difficulty,
        status=obj.status,
        course_id=obj.course_id,
        enterprise_id=obj.enterprise_id,
        course_name=obj.course.name if obj.course else None,
        enterprise_name=obj.enterprise.name if obj.enterprise else None,
        created_by=obj.created_by,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.get("", response_model=PageResult[QuestionOut])
def list_questions(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("list.question"))],
    page: Annotated[PageParams, Depends()],
    q_type: str | None = None,
    status: str | None = None,
    course_id: int | None = None,
    stem_keyword: str | None = Query(default=None, description="题干模糊匹配"),
) -> PageResult[QuestionOut]:
    """题目列表。"""
    sk = (stem_keyword or "").strip()
    stem_like = f"%{sk}%" if sk else None

    stmt = select(func.count()).select_from(Question).join(User, Question.created_by == User.id)
    stmt = restrict_query_by_creator_enterprise(stmt, current)
    if q_type:
        stmt = stmt.where(Question.q_type == q_type)
    if status:
        stmt = stmt.where(Question.status == status)
    if course_id is not None:
        stmt = stmt.where(Question.course_id == course_id)
    if stem_like is not None:
        stmt = stmt.where(Question.stem.like(stem_like))
    total = db.scalar(stmt) or 0
    q = select(Question).join(User, Question.created_by == User.id)
    q = restrict_query_by_creator_enterprise(q, current)
    if q_type:
        q = q.where(Question.q_type == q_type)
    if status:
        q = q.where(Question.status == status)
    if course_id is not None:
        q = q.where(Question.course_id == course_id)
    if stem_like is not None:
        q = q.where(Question.stem.like(stem_like))
    q = q.options(joinedload(Question.course), joinedload(Question.enterprise))
    rows = db.scalars(q.offset(page.skip).limit(page.limit).order_by(Question.id.desc())).all()
    return PageResult[QuestionOut](total=int(total), items=[_to_out(r) for r in rows])


@router.post("/batch-publish", response_model=dict)
def batch_publish_questions(
    body: QuestionBatchPublishIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.batch"))],
) -> dict:
    """批量发布：将草稿改为已发布。"""
    n_ok = 0
    for qid in body.ids:
        obj = db.get(Question, qid)
        if obj is None:
            continue
        try:
            assert_question_in_enterprise(db, current, qid)
        except HTTPException:
            continue
        if obj.status != "published":
            obj.status = "published"
            n_ok += 1
    db.commit()
    return {"updated": n_ok}


@router.post("/import", response_model=QuestionImportResult)
async def import_questions(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.import"))],
    course_id: Annotated[int, Form()],
    enterprise_id: Annotated[int, Form()],
    file: UploadFile = File(...),
) -> QuestionImportResult:
    """导入题库：解析文件并写入草稿题目。"""
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    ent = db.get(Enterprise, enterprise_id)
    if ent is None:
        raise HTTPException(status_code=404, detail="企业不存在")
    if course.enterprise_id != enterprise_id:
        raise HTTPException(status_code=400, detail="课程与所属企业不一致")
    if not is_super_role(current):
        if current.enterprise_id is None or current.enterprise_id != enterprise_id:
            raise HTTPException(status_code=403, detail="无权导入到该企业")
    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件超过 20MB")
    fn = file.filename or "upload"
    ext = (fn.rsplit(".", 1)[-1] if "." in fn else "").lower()
    image_ext = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
    try:
        if ext in image_ext:
            items = [build_image_placeholder(fn)]
        else:
            try:
                text = extract_plain_text(fn, raw)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            except ModuleNotFoundError as e:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"服务端未安装解析依赖「{e.name}」。"
                        "请在 api 容器内执行 pip install -r requirements.txt（需含 pypdf、openpyxl、python-docx）后重建镜像。"
                    ),
                ) from e
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"读取或解析文件失败：{e!s}") from e
            if not text.strip():
                items = [build_image_placeholder(fn)]
            else:
                try:
                    items = build_questions_from_text(text)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"题目文本切分失败：{e!s}") from e
        if not items:
            raise HTTPException(status_code=400, detail="未能从文件中解析出题目")
        created = 0
        for it in items:
            stem = (it.get("stem") or "").strip()
            if not stem:
                continue
            if len(stem) > 2000:
                stem = stem[:2000]
            q_type = it.get("q_type") or "single"
            qn = allocate_question_no(db, enterprise_id, course_id, q_type)
            obj = Question(
                question_no=qn,
                q_type=q_type,
                stem=stem,
                options_json=it.get("options_json"),
                answer_json=it["answer_json"] if it.get("answer_json") is not None else {"choice": "A"},
                analysis=normalize_analysis(it.get("analysis")),
                difficulty=1,
                status="draft",
                course_id=course_id,
                enterprise_id=enterprise_id,
                created_by=current.id,
            )
            db.add(obj)
            db.flush()
            created += 1
        if created == 0:
            raise HTTPException(status_code=400, detail="解析结果中无有效题干，请检查文件是否为题目格式或换源文件重试")
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="题号或唯一约束冲突（可能重复导入），请刷新后重试",
        ) from e
    except (OperationalError, ProgrammingError) as e:
        db.rollback()
        orig = getattr(e, "orig", None)
        msg = str(orig) if orig is not None else str(e)
        if "question_no" in msg or "Unknown column" in msg:
            raise HTTPException(
                status_code=503,
                detail="数据库结构未升级：请在服务器执行 alembic upgrade head（含 question_no 字段）后重试",
            ) from e
        raise HTTPException(status_code=503, detail=f"数据库错误：{msg}") from e
    except Exception as e:
        db.rollback()
        logger.exception("题库导入失败")
        raise HTTPException(status_code=500, detail=f"导入失败：{e!s}") from e
    return QuestionImportResult(created=created, message=f"已导入 {created} 道题目草稿")


@router.post("", response_model=QuestionOut)
def create_question(
    body: QuestionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.manage"))],
) -> QuestionOut:
    """新增题目。"""
    qn = allocate_question_no(db, body.enterprise_id, body.course_id, body.q_type)
    obj = Question(
        question_no=qn,
        q_type=body.q_type,
        stem=body.stem,
        options_json=body.options_json,
        answer_json=body.answer_json,
        analysis=body.analysis,
        difficulty=body.difficulty,
        status=body.status,
        course_id=body.course_id,
        enterprise_id=body.enterprise_id,
        created_by=current.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    obj = db.scalars(
        select(Question)
        .options(joinedload(Question.course), joinedload(Question.enterprise))
        .where(Question.id == obj.id)
    ).first()
    return _to_out(obj)


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(
    question_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User,
        Depends(require_any_permission("list.question", "action.question.manage")),
    ],
) -> QuestionOut:
    obj = assert_question_in_enterprise(db, current, question_id)
    obj = db.scalars(
        select(Question)
        .options(joinedload(Question.course), joinedload(Question.enterprise))
        .where(Question.id == question_id)
    ).first()
    assert obj is not None
    return _to_out(obj)


@router.patch("/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    body: QuestionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.manage"))],
) -> QuestionOut:
    obj = assert_question_in_enterprise(db, current, question_id)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    obj = db.scalars(
        select(Question)
        .options(joinedload(Question.course), joinedload(Question.enterprise))
        .where(Question.id == question_id)
    ).first()
    assert obj is not None
    return _to_out(obj)


@router.delete("/{question_id}", status_code=204)
def delete_question(
    question_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.manage"))],
) -> None:
    obj = assert_question_in_enterprise(db, current, question_id)
    db.delete(obj)
    db.commit()
