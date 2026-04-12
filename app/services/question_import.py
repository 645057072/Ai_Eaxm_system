# -*- coding: utf-8 -*-
"""题库文件解析：按文本块推断题型并生成草稿题目结构。"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Word / Excel / PDF
def _text_from_txt_csv(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


def _text_from_xlsx(raw: bytes) -> str:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb.active
    lines: List[str] = []
    for row in ws.iter_rows(values_only=True):
        lines.append("\t".join("" if c is None else str(c).strip() for c in row))
    return "\n".join(lines)


def _text_from_docx(raw: bytes) -> str:
    import docx

    doc = docx.Document(io.BytesIO(raw))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _text_from_pdf(raw: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(raw))
    parts: List[str] = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def extract_plain_text(filename: str, raw: bytes) -> str:
    """从上传文件提取纯文本；图片等非文本返回空串，由上层生成占位题干。"""
    ext = Path(filename).suffix.lower()
    if ext in (".txt",):
        return _text_from_txt_csv(raw)
    if ext == ".csv":
        # 首列拼接为可读文本块
        text = _text_from_txt_csv(raw)
        lines = []
        try:
            for row in csv.reader(io.StringIO(text)):
                if row:
                    lines.append(row[0].strip())
        except Exception:
            return text
        return "\n".join(lines)
    if ext == ".xlsx":
        return _text_from_xlsx(raw)
    if ext == ".docx":
        return _text_from_docx(raw)
    if ext == ".pdf":
        return _text_from_pdf(raw)
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        return ""
    raise ValueError(f"不支持的扩展名: {ext}")


def _split_blocks(text: str) -> List[str]:
    t = text.strip()
    if not t:
        return []
    # 按双换行或 数字开头的新题切分
    parts = re.split(r"(?:\n\s*){2,}|(?=\n\s*\d{1,3}[\.\)、]\s*\S)", t)
    out = [p.strip() for p in parts if p.strip()]
    if len(out) <= 1 and "\n" in t:
        out = [ln.strip() for ln in t.splitlines() if ln.strip()]
    return out if out else [t]


def _parse_option_lines(lines: List[str]) -> Tuple[List[Dict[str, str]], List[str]]:
    """解析 A. B. C. 选项行。"""
    opts: List[Dict[str, str]] = []
    stem_lines: List[str] = []
    opt_pat = re.compile(r"^\s*([A-Za-z])[\.\、:：]\s*(.+)$")
    for ln in lines:
        m = opt_pat.match(ln.strip())
        if m:
            k = m.group(1).upper()
            opts.append({"key": k, "text": m.group(2).strip()})
        else:
            stem_lines.append(ln)
    return opts, stem_lines


def classify_and_build(stem_text: str) -> Dict[str, Any]:
    """根据内容推断题型并构造 options_json / answer_json（草稿可后续人工修订）。"""
    lines = [ln.strip() for ln in stem_text.splitlines() if ln.strip()]
    if not lines:
        return {
            "q_type": "single",
            "stem": stem_text or "（空题干）",
            "options_json": [{"key": "A", "text": "选项A"}, {"key": "B", "text": "选项B"}],
            "answer_json": {"choice": "A"},
        }
    full = "\n".join(lines)
    # 判断题
    if re.search(r"判断题|对的打|错的打|正确|错误|\(\s*\)|（\s*）", full) and len(lines) <= 6:
        return {
            "q_type": "judge",
            "stem": lines[0],
            "options_json": [{"key": "T", "text": "正确"}, {"key": "F", "text": "错误"}],
            "answer_json": {"choice": "T"},
        }
    opts, stem_lines = _parse_option_lines(lines)
    stem = "\n".join(stem_lines) if stem_lines else lines[0]
    if "多选" in full or "多项选择" in full:
        return {
            "q_type": "multiple",
            "stem": stem,
            "options_json": opts
            if opts
            else [{"key": "A", "text": "选项A"}, {"key": "B", "text": "选项B"}, {"key": "C", "text": "选项C"}],
            "answer_json": {"choices": ["A", "B"]},
        }
    if "____" in full or "填空" in full or re.search(r"（\s{2,}|_{3,}", full):
        return {
            "q_type": "fill",
            "stem": full,
            "options_json": None,
            "answer_json": {"text": ""},
        }
    if len(opts) >= 2:
        return {
            "q_type": "single",
            "stem": stem,
            "options_json": opts,
            "answer_json": {"choice": opts[0]["key"]},
        }
    return {
        "q_type": "single",
        "stem": full,
        "options_json": [
            {"key": "A", "text": "选项A"},
            {"key": "B", "text": "选项B"},
            {"key": "C", "text": "选项C"},
            {"key": "D", "text": "选项D"},
        ],
        "answer_json": {"choice": "A"},
    }


def build_questions_from_text(text: str) -> List[Dict[str, Any]]:
    blocks = _split_blocks(text)
    if not blocks:
        return []
    return [classify_and_build(b) for b in blocks]


def build_image_placeholder(filename: str) -> Dict[str, Any]:
    """图片文件无文本时生成占位草稿，便于后续人工维护。"""
    return {
        "q_type": "single",
        "stem": f"【图片导入】{filename}：请编辑题干与选项",
        "options_json": [{"key": "A", "text": "选项A"}, {"key": "B", "text": "选项B"}],
        "answer_json": {"choice": "A"},
        "analysis": "图片导入占位，请人工完善题目内容",
    }
