# -*- coding: utf-8 -*-
"""题库文件解析：按文本块推断题型并生成草稿题目结构。"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 题干最大字符数（与接口校验一致）
STEM_MAX_LEN = 2000
# 解析字段最大字符数（MySQL TEXT 约 64KB；UTF-8 下单字段不宜过长）
ANALYSIS_MAX_LEN = 16000


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


def _truncate_stem(s: str) -> str:
    s = s.strip()
    if len(s) <= STEM_MAX_LEN:
        return s
    return s[:STEM_MAX_LEN]


def _crop_analysis_body(raw: str) -> str:
    """截取「解析」正文，遇下一题题号或下一道答案行时截断，避免误吞整卷。"""
    if not raw:
        return ""
    lines_out: List[str] = []
    for line in raw.splitlines():
        st = line.strip()
        if lines_out:
            # 下一道题常见行首：数字+点/顿号+正文
            if re.match(r"^\d{1,3}[\.\)、]\s*\S", st):
                break
            # 下一题的「答案：」误入解析区
            if re.match(r"^(?:答案|标准答案)[：:]", st):
                break
        elif re.match(r"^\d{1,3}[\.\)、]\s*\S", st):
            # 解析区首行即像下一题题号，视为无有效解析
            return ""
        lines_out.append(line)
    return "\n".join(lines_out).strip()


def _truncate_analysis(s: str) -> Optional[str]:
    """解析入库前截断长度。"""
    s = s.strip()
    if not s:
        return None
    if len(s) > ANALYSIS_MAX_LEN:
        return s[:ANALYSIS_MAX_LEN]
    return s


def normalize_analysis(value: Optional[str]) -> Optional[str]:
    """供 API 入库前统一限制解析长度（与导入解析逻辑一致）。"""
    if value is None:
        return None
    return _truncate_analysis(value)


def _split_answer_analysis(text: str) -> Tuple[str, Optional[str], Optional[str]]:
    """从整段文本去掉「答案」「解析」行块，仅保留题目与选项部分。"""
    t = text.strip()
    aw: Optional[str] = None
    an: Optional[str] = None
    # 先去掉「解析：…」：不可贪婪到全文末尾，需按下一题边界裁剪后再截断长度
    m_p = re.search(r"(?:^|\n)\s*解析[：:]\s*", t)
    if m_p:
        rest = t[m_p.end() :]
        an = _truncate_analysis(_crop_analysis_body(rest))
        t = t[: m_p.start()].strip()
    # 再去掉「答案：」单行
    m_a = re.search(r"(?:^|\n)\s*(?:答案|标准答案)[：:]\s*([^\n]+)", t)
    if m_a:
        aw = m_a.group(1).strip()
        t = t[: m_a.start()].strip()
    return t, aw, an


def _parse_answer_to_json(ans: Optional[str], q_type: str) -> Any:
    """根据文本答案生成 answer_json。"""
    if not ans or not str(ans).strip():
        if q_type == "multiple":
            return {"choices": ["A"]}
        if q_type == "judge":
            return {"choice": "T"}
        if q_type == "fill":
            return {"text": ""}
        return {"choice": "A"}
    s = str(ans).strip()
    if q_type == "multiple":
        keys = re.findall(r"[A-E]", s.upper())
        return {"choices": keys if keys else ["A"]}
    if q_type == "judge":
        if any(x in s for x in ("错", "误", "否", "×")) or s in ("错误", "不正确", "F"):
            return {"choice": "F"}
        if any(x in s for x in ("对", "是", "正确", "√", "T", "真")):
            return {"choice": "T"}
        return {"choice": "T"}
    if q_type == "fill":
        return {"text": s}
    m = re.match(r"^([A-Ea-e])", s)
    if m:
        return {"choice": m.group(1).upper()}
    return {"choice": "A"}


def _parse_option_lines(lines: List[str]) -> Tuple[List[Dict[str, str]], List[str]]:
    """解析 A. B. C. 选项行。"""
    opts: List[Dict[str, str]] = []
    stem_lines: List[str] = []
    opt_pat = re.compile(r"^\s*([A-Ea-e])[\.\．、:：]\s*(.+)$")
    for ln in lines:
        m = opt_pat.match(ln.strip())
        if m:
            k = m.group(1).upper()
            opts.append({"key": k, "text": m.group(2).strip()})
        else:
            stem_lines.append(ln)
    return opts, stem_lines


def _infer_qtype(stem_core: str, opts: List[Dict[str, str]], hint: str) -> str:
    full = hint
    if re.search(r"判断题|对的打|错的打", full) and len(opts) <= 2:
        return "judge"
    if "多选" in full or "多项选择" in full:
        return "multiple"
    if "____" in full or "填空" in full or re.search(r"_{3,}|（\s{2,}", full):
        return "fill"
    if len(opts) >= 2:
        return "single"
    if re.search(r"正确|错误|对错", stem_core) and len(opts) < 2:
        return "judge"
    return "single"


def _is_noise_block(block: str) -> bool:
    """非题目说明、章节标题等不入库。"""
    t = block.strip()
    if len(t) < 12:
        return True
    # 仅「一、单选题」类标题
    if re.match(r"^[一二三四五六七八九十百千]+[、．.].{0,40}$", t) and "？" not in t and "?" not in t:
        return True
    if re.match(r"^[（(]\s*[一二三四五六七八九十]+\s*[）)]", t) and len(t) < 60:
        return True
    # 无 A. B. 选项、无问号、无填空特征：整段视为封面/前言/目录，不保存
    if not re.search(r"[A-E][\.．、]\s*\S", t):
        if "？" not in t and "?" not in t and "____" not in t and "填空" not in t:
            return True
    if re.search(r"模拟题|理论部分|考试说明", t) and not re.search(r"[A-E][\.．、]", t):
        if "？" not in t and "?" not in t:
            return True
    return False


def _split_blocks(text: str) -> List[str]:
    t = text.strip()
    if not t:
        return []
    # 按空行或「行首题号+内容」切题
    parts = re.split(r"(?:\n\s*){2,}|(?=\n\s*\d{1,3}[\.\)、]\s)", t)
    out = [p.strip() for p in parts if p.strip()]
    if len(out) <= 1 and "\n" in t:
        parts2 = re.split(r"(?=\n\s*\d{1,3}[\.\)、]\s)", t)
        out = [p.strip() for p in parts2 if p.strip()]
    return out if out else [t]


def _strip_leading_qnum(s: str) -> str:
    """去掉行首题号如 1. 2、"""
    return re.sub(r"^\s*\d{1,3}[\.\)、]\s*", "", s.strip(), count=1)


def parse_question_block(block: str) -> Optional[Dict[str, Any]]:
    """解析单题：题干不含答案/解析；答案与解析分字段。"""
    if _is_noise_block(block):
        return None
    body, aw_raw, an_raw = _split_answer_analysis(block)
    lines = [ln for ln in body.splitlines() if ln.strip()]
    if not lines:
        return None
    opts, stem_lines = _parse_option_lines(lines)
    stem_core = "\n".join(stem_lines).strip()
    stem_core = _strip_leading_qnum(stem_core)
    hint = body
    q_type = _infer_qtype(stem_core, opts, hint)

    if q_type == "fill":
        stem = _truncate_stem(stem_core if stem_core else body[:STEM_MAX_LEN])
        return {
            "q_type": "fill",
            "stem": stem,
            "options_json": None,
            "answer_json": _parse_answer_to_json(aw_raw, "fill"),
            "analysis": an_raw,
        }

    if q_type == "judge":
        stem = _truncate_stem(stem_core if stem_core else "\n".join(lines[:3]))
        opts_use = (
            opts
            if len(opts) >= 2
            else [{"key": "T", "text": "正确"}, {"key": "F", "text": "错误"}]
        )
        return {
            "q_type": "judge",
            "stem": stem,
            "options_json": opts_use,
            "answer_json": _parse_answer_to_json(aw_raw, "judge"),
            "analysis": an_raw,
        }

    stem = _truncate_stem(stem_core if stem_core else (lines[0] if lines else "（题干）"))
    if len(opts) < 2:
        # 无选项时退化为单选占位
        return {
            "q_type": "single",
            "stem": stem,
            "options_json": [
                {"key": "A", "text": "选项A"},
                {"key": "B", "text": "选项B"},
                {"key": "C", "text": "选项C"},
                {"key": "D", "text": "选项D"},
            ],
            "answer_json": _parse_answer_to_json(aw_raw, "single"),
            "analysis": an_raw,
        }

    ans_j = _parse_answer_to_json(aw_raw, q_type)
    return {
        "q_type": q_type,
        "stem": stem,
        "options_json": opts,
        "answer_json": ans_j,
        "analysis": an_raw,
    }


def build_questions_from_text(text: str) -> List[Dict[str, Any]]:
    blocks = _split_blocks(text)
    out: List[Dict[str, Any]] = []
    for b in blocks:
        try:
            item = parse_question_block(b)
            if item:
                out.append(item)
        except Exception:
            # 单块解析异常不拖垮整份文件
            continue
    return out


def build_image_placeholder(filename: str) -> Dict[str, Any]:
    """图片文件无文本时生成占位草稿，便于后续人工维护。"""
    return {
        "q_type": "single",
        "stem": f"【图片导入】{filename}：请编辑题干与选项",
        "options_json": [{"key": "A", "text": "选项A"}, {"key": "B", "text": "选项B"}],
        "answer_json": {"choice": "A"},
        "analysis": None,
    }
