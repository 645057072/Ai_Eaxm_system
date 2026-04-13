# -*- coding: utf-8 -*-
"""题目内容去重：同一企业、课程下题干/选项/答案/解析一致视为重复。"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.question import Question


def _canonical_json(obj: Any) -> str:
    """稳定序列化，用于指纹计算。"""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def _normalize_options_for_dedup(options_json: Any) -> Any:
    if options_json is None:
        return None
    if not isinstance(options_json, list):
        return options_json
    out = []
    for o in options_json:
        if isinstance(o, dict):
            k = str(o.get("key", "")).strip().upper()
            t = str(o.get("text", "")).strip()
            out.append({"key": k, "text": t})
        else:
            out.append(o)
    return sorted(out, key=lambda x: str(x.get("key", "")) if isinstance(x, dict) else str(x))


def compute_question_dedup_hash(
    enterprise_id: Optional[int],
    course_id: Optional[int],
    q_type: str,
    stem: str,
    options_json: Any,
    answer_json: Any,
    analysis: Optional[str],
) -> Optional[str]:
    """计算去重指纹；企业或课程为空时不写入指纹（不参与唯一约束）。"""
    if enterprise_id is None or course_id is None:
        return None
    payload = {
        "e": int(enterprise_id),
        "c": int(course_id),
        "t": (q_type or "").strip(),
        "s": (stem or "").strip(),
        "o": _normalize_options_for_dedup(options_json),
        "a": answer_json,
        "n": (analysis or "").strip(),
    }
    raw = _canonical_json(payload)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def find_duplicate_question_id(
    db: Session,
    enterprise_id: Optional[int],
    course_id: Optional[int],
    q_type: str,
    stem: str,
    options_json: Any,
    answer_json: Any,
    analysis: Optional[str],
    exclude_id: Optional[int] = None,
) -> Optional[int]:
    """若存在相同指纹题目则返回其 id，否则 None。"""
    h = compute_question_dedup_hash(enterprise_id, course_id, q_type, stem, options_json, answer_json, analysis)
    if h is None:
        return None
    q = select(Question.id).where(
        Question.enterprise_id == enterprise_id,
        Question.course_id == course_id,
        Question.dedup_hash == h,
    )
    if exclude_id is not None:
        q = q.where(Question.id != exclude_id)
    return db.scalar(q.limit(1))
