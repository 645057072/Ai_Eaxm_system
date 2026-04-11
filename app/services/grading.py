# -*- coding: utf-8 -*-
"""客观题自动阅卷。"""

from decimal import Decimal
from typing import Any, Optional

from app.models.question import Question


def score_for_question(question: Question, user_answer: Any, full_score: Decimal) -> Decimal:
    """客观题：全对得满分，否则 0 分。"""
    if _is_correct(question, user_answer):
        return full_score
    return Decimal("0")


def _is_correct(question: Question, user_answer: Any) -> bool:
    std = question.answer_json
    q_type = question.q_type

    if q_type == "judge":
        return _norm_bool(user_answer) == _norm_bool(std)

    if q_type == "single":
        return str(user_answer or "").strip().upper() == str(std or "").strip().upper()

    if q_type == "multiple":
        return _as_sorted_list(user_answer) == _as_sorted_list(std)

    if q_type == "fill":
        return str(user_answer or "").strip() == str(std or "").strip()

    return False


def _norm_bool(v: Any) -> Optional[bool]:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("true", "1", "yes", "正确"):
        return True
    if s in ("false", "0", "no", "错误"):
        return False
    return None


def _as_sorted_list(v: Any) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return sorted(str(x).strip().upper() for x in v)
    return sorted([str(v).strip().upper()])
