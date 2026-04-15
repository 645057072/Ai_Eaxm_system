# -*- coding: utf-8 -*-
"""基于大语言模型的题库导入解析（将原始文本转为结构化题目）。"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import get_settings


def _normalize_q_type(v: str) -> str:
    s = (v or "").strip().lower()
    if s in ("judge", "判断", "判断题"):
        return "judge"
    if s in ("single", "单选", "单选题"):
        return "single"
    if s in ("multiple", "多选", "多选题"):
        return "multiple"
    if s in ("fill", "填空", "填空题"):
        return "fill"
    return "single"


def _normalize_options(raw: Any) -> Optional[list[dict[str, str]]]:
    if raw is None:
        return None
    if not isinstance(raw, list):
        return None
    out: list[dict[str, str]] = []
    for it in raw:
        if not isinstance(it, dict):
            continue
        k = str(it.get("key") or "").strip().upper()
        t = str(it.get("text") or "").strip()
        if not k or not t:
            continue
        out.append({"key": k, "text": t})
    return out or None


def _normalize_answer(q_type: str, raw: Any) -> Any:
    if q_type == "judge":
        if raw is True or raw is False:
            return bool(raw)
        s = str(raw or "").strip()
        if s in ("正确", "对", "T", "True", "true", "1", "√"):
            return True
        if s in ("错误", "错", "F", "False", "false", "0", "×"):
            return False
        return True
    if q_type == "multiple":
        if isinstance(raw, list):
            keys = [str(x).strip().upper() for x in raw if str(x).strip()]
            return keys or ["A"]
        s = str(raw or "").strip().upper()
        keys = [c for c in s if c in "ABCDE"]
        return keys or ["A"]
    if q_type == "fill":
        return str(raw or "")
    # single
    s = str(raw or "").strip().upper()
    if s and s[0] in "ABCDE":
        return s[0]
    return "A"


def llm_parse_questions_from_text(text: str) -> Tuple[list[dict[str, Any]], list[str]]:
    """调用大模型解析整段文本，返回 items 与日志。"""
    st = get_settings()
    if not getattr(st, "llm_enabled", False):
        return [], ["[LLM] 未启用"]
    base = (getattr(st, "llm_api_base", "") or "").strip().rstrip("/")
    key = (getattr(st, "llm_api_key", "") or "").strip()
    model = (getattr(st, "llm_model", "") or "").strip()
    if not base or not key or not model:
        raise ValueError("LLM 未配置：请设置 LLM_API_BASE / LLM_API_KEY / LLM_MODEL 并启用 LLM_ENABLED=1")

    sys = (
        "你是题库导入解析器。请将用户提供的试卷/题库文本解析为结构化题目 JSON 数组。"
        "要求：\n"
        "- 题型仅允许 judge/single/multiple/fill\n"
        "- single/multiple 必须给出 options_json（A-E）与 answer_json\n"
        "- judge 的 answer_json 为 true/false\n"
        "- fill 的 answer_json 为字符串\n"
        "- analysis 可选\n"
        "输出必须是严格 JSON（不要 Markdown，不要解释）。"
    )
    user = (
        "请解析以下文本为题目数组。每个元素结构：\n"
        "{\n"
        "  \"q_type\": \"single|multiple|judge|fill\",\n"
        "  \"stem\": \"题干\",\n"
        "  \"options_json\": [{\"key\":\"A\",\"text\":\"...\"}, ...] | null,\n"
        "  \"answer_json\": \"A\" | [\"A\",\"C\"] | true | false | \"填空答案\",\n"
        "  \"analysis\": \"解析\" | null\n"
        "}\n"
        "文本如下：\n"
        + text
    )

    url = base + "/v1/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }

    headers = {"Authorization": f"Bearer {key}"}
    with httpx.Client(timeout=90) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    content = (
        (data.get("choices") or [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    if not content:
        return [], ["[LLM] 返回内容为空"]
    obj = json.loads(content)
    arr = obj.get("items") if isinstance(obj, dict) and "items" in obj else obj
    if not isinstance(arr, list):
        raise ValueError("LLM 输出不是数组")

    items: list[dict[str, Any]] = []
    for it in arr:
        if not isinstance(it, dict):
            continue
        qt = _normalize_q_type(str(it.get("q_type") or "single"))
        stem = str(it.get("stem") or "").strip()
        if not stem:
            continue
        opts = _normalize_options(it.get("options_json"))
        ans = _normalize_answer(qt, it.get("answer_json"))
        analysis = it.get("analysis")
        an = str(analysis).strip() if analysis is not None and str(analysis).strip() else None
        items.append(
            {
                "q_type": qt,
                "stem": stem,
                "options_json": opts,
                "answer_json": ans,
                "analysis": an,
            }
        )
    return items, [f"[LLM] 解析题目数：{len(items)}"]

