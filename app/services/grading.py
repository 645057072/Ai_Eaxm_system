# -*- coding: utf-8 -*-
"""客观题自动阅卷。"""

from decimal import Decimal
from typing import Any, Optional

from app.models.question import Question


def answer_provided(question: Question, user_answer: Any) -> bool:
    """是否视为考生已作答（未答题不写入练习报告）。"""
    qt = (question.q_type or "").strip()
    if user_answer is None:
        return False
    if qt == "judge":
        if isinstance(user_answer, bool):
            return True
        return str(user_answer).strip() != ""
    if qt == "multiple":
        if isinstance(user_answer, list):
            return len(user_answer) > 0
        return str(user_answer).strip() != ""
    if qt in ("single", "fill"):
        return str(user_answer).strip() != ""
    return str(user_answer).strip() != ""


def score_for_question(question: Question, user_answer: Any, full_score: Decimal) -> Decimal:
    """客观题：全对得满分，否则 0 分。"""
    if _is_correct(question, user_answer):
        return full_score
    return Decimal("0")


def is_correct(question: Question, user_answer: Any) -> bool:
    """是否答对（错题练习移除用）。"""
    return _is_correct(question, user_answer)


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
