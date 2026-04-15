# -*- coding: utf-8 -*-

import logging
from collections import Counter
from datetime import datetime
from typing import Annotated, List

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
    QuestionBatchDeleteIn,
    QuestionBatchDifficultyIn,
    QuestionBatchIdsIn,
    QuestionBatchPublishIn,
    QuestionCreate,
    QuestionImportResult,
    QuestionNeighborsOut,
    QuestionOut,
    QuestionUpdate,
)
from app.services.data_scope import (
    assert_question_in_enterprise,
    get_managed_enterprise_ids,
    restrict_questions_query_by_tenant,
    ensure_in_managed_enterprise_scope,
)
from app.services.question_number import allocate_question_no
from app.services.question_dedup import compute_question_dedup_hash, find_duplicate_question_id
from app.services.question_import import (
    build_image_placeholder,
    build_questions_from_excel_table,
    build_questions_from_uploaded_texts,
    extract_plain_text,
)
from app.services.llm_question_import import llm_parse_questions_from_text
from app.core.config import get_settings

router = APIRouter()

_ALLOWED_Q_STATUS = frozenset({"draft", "published", "disabled"})


def _validate_status_transition(old: str, new: str) -> None:
    """题目状态变更：未发布不得设为禁用；禁用仅可反禁用为已发布。"""
    if new not in _ALLOWED_Q_STATUS:
        raise HTTPException(status_code=400, detail=f"非法状态：{new}，仅支持 draft / published / disabled")
    allowed = {
        ("draft", "draft"),
        ("draft", "published"),
        ("published", "published"),
        ("published", "draft"),
        ("published", "disabled"),
        ("disabled", "disabled"),
        ("disabled", "published"),
    }
    if (old, new) not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"不允许从「{old}」变更为「{new}」：未发布不得禁用；禁用题目请使用反禁用恢复为已发布",
        )


def _assert_question_deletable(obj: Question) -> None:
    if obj.status == "draft":
        return
    if obj.status == "published":
        raise HTTPException(status_code=400, detail="已发布题目不可删除，请先反发布为草稿")
    if obj.status == "disabled":
        raise HTTPException(status_code=400, detail="已禁用题目不可删除，请先反禁用")
    raise HTTPException(status_code=400, detail=f"题目状态为「{obj.status}」，仅草稿可删除")


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


def _stem_like(stem_keyword: str | None) -> str | None:
    sk = (stem_keyword or "").strip()
    return f"%{sk}%" if sk else None


def _apply_question_list_filters(
    stmt,
    q_type: str | None,
    status: str | None,
    course_id: int | None,
    stem_like: str | None,
):
    if q_type:
        stmt = stmt.where(Question.q_type == q_type)
    if status:
        stmt = stmt.where(Question.status == status)
    if course_id is not None:
        stmt = stmt.where(Question.course_id == course_id)
    if stem_like is not None:
        stmt = stmt.where(Question.stem.like(stem_like))
    return stmt


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
    stem_like = _stem_like(stem_keyword)

    stmt = select(func.count()).select_from(Question).join(User, Question.created_by == User.id)
    stmt = restrict_questions_query_by_tenant(stmt, db, current)
    stmt = _apply_question_list_filters(stmt, q_type, status, course_id, stem_like)
    total = db.scalar(stmt) or 0
    q = select(Question).join(User, Question.created_by == User.id)
    q = restrict_questions_query_by_tenant(q, db, current)
    q = _apply_question_list_filters(q, q_type, status, course_id, stem_like)
    q = q.options(joinedload(Question.course), joinedload(Question.enterprise))
    rows = db.scalars(q.offset(page.skip).limit(page.limit).order_by(Question.id.desc())).all()
    return PageResult[QuestionOut](total=int(total), items=[_to_out(r) for r in rows])


@router.post("/batch-publish", response_model=dict)
def batch_publish_questions(
    body: QuestionBatchPublishIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.batch"))],
) -> dict:
    """批量发布：仅草稿可改为已发布。"""
    n_ok = 0
    for qid in body.ids:
        obj = db.get(Question, qid)
        if obj is None:
            continue
        try:
            assert_question_in_enterprise(db, current, qid)
        except HTTPException:
            continue
        if obj.status == "draft":
            obj.status = "published"
            n_ok += 1
    db.commit()
    return {"updated": n_ok}


@router.post("/batch-unpublish", response_model=dict)
def batch_unpublish_questions(
    body: QuestionBatchIdsIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.batch"))],
) -> dict:
    """批量反发布：已发布改为草稿。"""
    n_ok = 0
    for qid in body.ids:
        obj = db.get(Question, qid)
        if obj is None:
            continue
        try:
            assert_question_in_enterprise(db, current, qid)
        except HTTPException:
            continue
        if obj.status == "published":
            obj.status = "draft"
            n_ok += 1
    db.commit()
    return {"updated": n_ok}


@router.post("/batch-disable", response_model=dict)
def batch_disable_questions(
    body: QuestionBatchIdsIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.batch"))],
) -> dict:
    """批量禁用：仅已发布可改为禁用。"""
    n_ok = 0
    for qid in body.ids:
        obj = db.get(Question, qid)
        if obj is None:
            continue
        try:
            assert_question_in_enterprise(db, current, qid)
        except HTTPException:
            continue
        if obj.status == "published":
            obj.status = "disabled"
            n_ok += 1
    db.commit()
    return {"updated": n_ok}


@router.post("/batch-enable", response_model=dict)
def batch_enable_questions(
    body: QuestionBatchIdsIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.batch"))],
) -> dict:
    """批量反禁用：禁用恢复为已发布。"""
    n_ok = 0
    for qid in body.ids:
        obj = db.get(Question, qid)
        if obj is None:
            continue
        try:
            assert_question_in_enterprise(db, current, qid)
        except HTTPException:
            continue
        if obj.status == "disabled":
            obj.status = "published"
            n_ok += 1
    db.commit()
    return {"updated": n_ok}


@router.post("/batch-delete", response_model=dict)
def batch_delete_questions(
    body: QuestionBatchDeleteIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.manage"))],
) -> dict:
    """批量删除题目：仅草稿可删。"""
    n_ok = 0
    n_skip = 0
    for qid in body.ids:
        obj = db.get(Question, qid)
        if obj is None:
            continue
        try:
            assert_question_in_enterprise(db, current, qid)
        except HTTPException:
            continue
        if obj.status != "draft":
            n_skip += 1
            continue
        db.delete(obj)
        n_ok += 1
    db.commit()
    return {"deleted": n_ok, "skipped": n_skip}


@router.post("/batch-difficulty", response_model=dict)
def batch_update_difficulty(
    body: QuestionBatchDifficultyIn,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.manage"))],
) -> dict:
    """批量将选中题目的难度系数改为同一值。"""
    n_ok = 0
    for qid in body.ids:
        obj = db.get(Question, qid)
        if obj is None:
            continue
        try:
            assert_question_in_enterprise(db, current, qid)
        except HTTPException:
            continue
        obj.difficulty = body.difficulty
        n_ok += 1
    db.commit()
    return {"updated": n_ok}


@router.post("/import", response_model=QuestionImportResult)
async def import_questions(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.import"))],
    course_id: Annotated[int, Form()],
    enterprise_id: Annotated[int, Form()],
    files: Annotated[
        List[UploadFile] | None,
        File(description="可同时选择多个文件，表单字段名 files，按题号与答案册自动合并"),
    ] = None,
    file: Annotated[UploadFile | None, File(description="兼容单文件，字段名 file")] = None,
) -> QuestionImportResult:
    """导入题库：支持多文件；题干与「【参考答案】/【试题解析】」分册时按题号拼接后写入草稿。"""
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    ent = db.get(Enterprise, enterprise_id)
    if ent is None:
        raise HTTPException(status_code=404, detail="企业不存在")
    if course.enterprise_id != enterprise_id:
        raise HTTPException(status_code=400, detail="课程与所属企业不一致")
    if not is_super_role(current):
        managed = get_managed_enterprise_ids(db, current)
        if not managed or enterprise_id not in managed:
            raise HTTPException(status_code=403, detail="无权导入到该企业")
    upload_list: List[UploadFile] = []
    if files:
        upload_list.extend(files)
    if file is not None and (file.filename or "").strip():
        upload_list.append(file)
    if not upload_list:
        raise HTTPException(status_code=400, detail="请上传至少一个文件")
    image_ext = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
    per_file_max = 20 * 1024 * 1024
    total_max = 60 * 1024 * 1024
    try:
        raw_entries: list[tuple[str, bytes]] = []
        total_bytes = 0
        for uf in upload_list:
            raw = await uf.read()
            if len(raw) > per_file_max:
                raise HTTPException(status_code=400, detail=f"单个文件超过 20MB：{uf.filename or 'upload'}")
            total_bytes += len(raw)
            raw_entries.append((uf.filename or "upload", raw))
        if total_bytes > total_max:
            raise HTTPException(status_code=400, detail="多文件合计超过 60MB，请分批导入")
        text_sources: list[tuple[str, str]] = []
        image_items: list[dict] = []
        file_labels: list[str] = []
        for fn, raw in raw_entries:
            file_labels.append(fn)
            ext = (fn.rsplit(".", 1)[-1] if "." in fn else "").lower()
            if ext in image_ext:
                image_items.append(build_image_placeholder(fn))
                continue
            if ext in ("xls", "xlsx") and not get_settings().llm_enabled:
                excel_items, excel_logs = build_questions_from_excel_table(fn, raw)
                if excel_items:
                    parsed_items = []
                    text_sources = []
                    image_items.extend(excel_items)
                    merge_logs.extend(excel_logs)
                    continue
            try:
                text = extract_plain_text(fn, raw)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            except ModuleNotFoundError as e:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"服务端未安装解析依赖「{e.name}」。"
                        "请在 api 容器内执行 pip install -r requirements.txt（需含 pypdf、openpyxl、xlrd、python-docx）后重建镜像。"
                    ),
                ) from e
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"读取或解析文件失败：{e!s}") from e
            if not text.strip():
                image_items.append(build_image_placeholder(fn))
            else:
                text_sources.append((fn, text))
        merge_logs: list[str] = []
        if text_sources:
            # 若启用 LLM，则直接用 LLM 解析每份文本文件（不走规则推断）
            if get_settings().llm_enabled:
                parsed_items = []
                merge_logs = []
                for _fn, _txt in text_sources:
                    try:
                        items_one, logs_one = llm_parse_questions_from_text(_txt)
                    except Exception as e:
                        raise HTTPException(status_code=400, detail=f"LLM 解析失败：{e!s}") from e
                    parsed_items.extend(items_one)
                    merge_logs.extend(logs_one)
            else:
                try:
                    parsed_items, merge_logs = build_questions_from_uploaded_texts(text_sources)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"题目文本合并失败：{e!s}") from e
        else:
            parsed_items = []
        items = [*image_items, *parsed_items]
        if not items:
            raise HTTPException(status_code=400, detail="未能从文件中解析出题目")
        _qtype_cn = {"single": "单选", "multiple": "多选", "judge": "判断", "fill": "填空"}
        log_lines: list[str] = [
            f"导入时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"文件数：{len(upload_list)} 名称：{', '.join(file_labels)}",
            f"企业ID：{enterprise_id} 课程ID：{course_id}",
            "",
        ]
        if merge_logs:
            log_lines.extend(merge_logs)
            log_lines.append("")
        created = 0
        skipped_duplicate = 0
        failed = 0
        by_type: Counter[str] = Counter()
        for idx, it in enumerate(items, start=1):
            stem = (it.get("stem") or "").strip()
            q_type = it.get("q_type") or "single"
            opts = it.get("options_json")
            ans = it["answer_json"] if it.get("answer_json") is not None else "A"
            an = it.get("analysis")
            if not stem:
                failed += 1
                log_lines.append(f"[失败] 第{idx}道 题干为空，跳过")
                continue
            if len(stem) > 2000:
                stem = stem[:2000]
            dup_id = find_duplicate_question_id(
                db, enterprise_id, course_id, q_type, stem, opts, ans, an
            )
            if dup_id:
                skipped_duplicate += 1
                log_lines.append(
                    f"[跳过-重复] 第{idx}道 题型={q_type} 与已有题目ID={dup_id}内容相同 题干摘要={stem[:100]}"
                )
                continue
            try:
                with db.begin_nested():
                    dhash = compute_question_dedup_hash(
                        enterprise_id, course_id, q_type, stem, opts, ans, an
                    )
                    qn = allocate_question_no(db, enterprise_id, course_id, q_type)
                    obj = Question(
                        question_no=qn,
                        q_type=q_type,
                        stem=stem,
                        options_json=opts,
                        answer_json=ans,
                        analysis=an,
                        dedup_hash=dhash,
                        difficulty=1,
                        status="draft",
                        course_id=course_id,
                        enterprise_id=enterprise_id,
                        created_by=current.id,
                    )
                    db.add(obj)
                    db.flush()
                created += 1
                by_type[q_type] += 1
                log_lines.append(f"[成功] 第{idx}道 题号={qn} 题型={q_type}")
            except Exception as ex:
                failed += 1
                log_lines.append(f"[失败] 第{idx}道 题型={q_type} 题干摘要={stem[:100]} 原因：{ex!s}")
        if created == 0 and skipped_duplicate == 0 and failed == 0:
            raise HTTPException(
                status_code=400,
                detail="解析结果中无有效题干，请检查文件是否为题目格式或换源文件重试",
            )
        db.commit()
        log_lines.append("")
        log_lines.append(
            f"汇总：成功 {created} 题，重复跳过 {skipped_duplicate} 题，失败 {failed} 题。"
        )
        if by_type:
            bt = "，".join(
                f"{_qtype_cn.get(k, k)} {v} 题" for k, v in sorted(by_type.items(), key=lambda x: x[0])
            )
            log_lines.append(f"按题型成功：{bt}")
        log_text = "\n".join(log_lines)
        msg_parts: list[str] = []
        if created:
            bt = "，".join(
                f"{_qtype_cn.get(k, k)}{v}题" for k, v in sorted(by_type.items(), key=lambda x: x[0])
            )
            msg_parts.append(f"成功导入 {created} 题（{bt}）")
        if skipped_duplicate:
            msg_parts.append(f"重复跳过 {skipped_duplicate} 题")
        if failed:
            msg_parts.append(f"失败 {failed} 题（详见日志）")
        message = "；".join(msg_parts) if msg_parts else "未完成有效导入"
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
        if "question_no" in msg or "dedup_hash" in msg or "Unknown column" in msg:
            raise HTTPException(
                status_code=503,
                detail="数据库结构未升级：请在服务器执行 alembic upgrade head（含 question_no、dedup_hash 等字段）后重试",
            ) from e
        raise HTTPException(status_code=503, detail=f"数据库错误：{msg}") from e
    except Exception as e:
        db.rollback()
        logger.exception("题库导入失败")
        raise HTTPException(status_code=500, detail=f"导入失败：{e!s}") from e
    return QuestionImportResult(
        created=created,
        skipped_duplicate=skipped_duplicate,
        failed=failed,
        by_type=dict(by_type),
        message=message,
        log_text=log_text,
    )


@router.post("", response_model=QuestionOut)
def create_question(
    body: QuestionCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(require_permission("action.question.manage"))],
) -> QuestionOut:
    """新增题目。"""
    if not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, body.enterprise_id)
    if body.status not in ("draft", "published"):
        raise HTTPException(status_code=400, detail="新建题目状态仅可为草稿或已发布，禁用请通过批量或编辑在已发布后再操作")
    if find_duplicate_question_id(
        db,
        body.enterprise_id,
        body.course_id,
        body.q_type,
        body.stem,
        body.options_json,
        body.answer_json,
        body.analysis,
    ):
        raise HTTPException(
            status_code=409,
            detail="题目已存在（同一企业、课程下题型、题干、选项、标准答案、解析一致），无需重复录入",
        )
    dhash = compute_question_dedup_hash(
        body.enterprise_id,
        body.course_id,
        body.q_type,
        body.stem,
        body.options_json,
        body.answer_json,
        body.analysis,
    )
    qn = allocate_question_no(db, body.enterprise_id, body.course_id, body.q_type)
    obj = Question(
        question_no=qn,
        q_type=body.q_type,
        stem=body.stem,
        options_json=body.options_json,
        answer_json=body.answer_json,
        analysis=body.analysis,
        dedup_hash=dhash,
        difficulty=body.difficulty,
        status=body.status,
        course_id=body.course_id,
        enterprise_id=body.enterprise_id,
        created_by=current.id,
    )
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="题目已存在（同一企业、课程下内容重复），无需重复录入",
        ) from None
    db.refresh(obj)
    obj = db.scalars(
        select(Question)
        .options(joinedload(Question.course), joinedload(Question.enterprise))
        .where(Question.id == obj.id)
    ).first()
    return _to_out(obj)


@router.get("/{question_id}/neighbors", response_model=QuestionNeighborsOut)
def get_question_neighbors(
    question_id: int,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[
        User,
        Depends(require_any_permission("list.question", "action.question.manage")),
    ],
    q_type: str | None = None,
    status: str | None = None,
    course_id: int | None = None,
    stem_keyword: str | None = Query(default=None, description="与题目列表查询条件一致"),
) -> QuestionNeighborsOut:
    """当前筛选条件下，同一排序（id 降序）中的上一题/下一题 id。"""
    assert_question_in_enterprise(db, current, question_id)
    stem_like = _stem_like(stem_keyword)
    q = select(Question.id).join(User, Question.created_by == User.id)
    q = restrict_questions_query_by_tenant(q, db, current)
    q = _apply_question_list_filters(q, q_type, status, course_id, stem_like)
    q = q.order_by(Question.id.desc())
    ids = list(db.scalars(q).all())
    try:
        idx = ids.index(question_id)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="当前筛选条件下未包含该题目，请调整筛选或与列表条件一致后再试",
        ) from None
    return QuestionNeighborsOut(
        prev_id=ids[idx - 1] if idx > 0 else None,
        next_id=ids[idx + 1] if idx < len(ids) - 1 else None,
        index=idx,
        total=len(ids),
    )


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
    if "enterprise_id" in data and data["enterprise_id"] is not None and not is_super_role(current):
        ensure_in_managed_enterprise_scope(db, current, int(data["enterprise_id"]))
    if "status" in data:
        _validate_status_transition(obj.status, data["status"])
    stem_u = data.get("stem", obj.stem)
    qtype_u = data.get("q_type", obj.q_type)
    opts_u = data.get("options_json", obj.options_json)
    ans_u = data.get("answer_json", obj.answer_json)
    an_u = data.get("analysis", obj.analysis)
    eid_u = data.get("enterprise_id", obj.enterprise_id)
    cid_u = data.get("course_id", obj.course_id)
    if find_duplicate_question_id(
        db,
        eid_u,
        cid_u,
        qtype_u,
        stem_u,
        opts_u,
        ans_u,
        an_u,
        exclude_id=question_id,
    ):
        raise HTTPException(
            status_code=409,
            detail="题目已存在（同一企业、课程下题型、题干、选项、标准答案、解析一致），无需重复保存",
        )
    for k, v in data.items():
        setattr(obj, k, v)
    obj.dedup_hash = compute_question_dedup_hash(
        obj.enterprise_id,
        obj.course_id,
        obj.q_type,
        obj.stem,
        obj.options_json,
        obj.answer_json,
        obj.analysis,
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="题目已存在（同一企业、课程下内容重复），无需重复保存",
        ) from None
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
    _assert_question_deletable(obj)
    db.delete(obj)
    db.commit()
