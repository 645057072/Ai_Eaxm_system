# -*- coding: utf-8 -*-
"""
从《生成式AI工程师（高级）理论模拟题》PDF 中仅读取指定页文本。
使用 PyMuPDF 按页号加载，不遍历全册、不做整本 OCR。

用法:
  python read_exam_pdf_pages.py --pdf "路径/生成式AI工程师（高级）理论模拟题.pdf"
  python read_exam_pdf_pages.py --pdf file.pdf --pages 2,3,78,150 --out sample_pages.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except ImportError:
    print("请先安装: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)


# 默认读取的页码（印刷/目录中的「第 N 页」，1 起算）
DEFAULT_PAGE_NUMBERS_ONE_BASED = (2, 3, 78, 150)


def one_based_to_index(page_no: int) -> int:
    """将「第 N 页」转为 PDF 内部 0 基索引。"""
    if page_no < 1:
        raise ValueError("页码须 >= 1")
    return page_no - 1


def extract_pages_text(
    pdf_path: Path,
    page_numbers_one_based: list[int],
) -> dict[str, Any]:
    """
    仅打开指定页并提取文本；不读取其它页内容。
    若某页超出文档总页数，该页记为错误信息。
    """
    path = pdf_path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"找不到 PDF: {path}")

    doc = fitz.open(path)
    total = doc.page_count
    result: dict[str, Any] = {
        "pdf": str(path),
        "total_pages_in_file": total,
        "pages": [],
    }

    for n in page_numbers_one_based:
        idx = one_based_to_index(n)
        entry: dict[str, Any] = {"page_one_based": n, "page_index": idx}
        if idx >= total:
            entry["error"] = f"超出文档页数（文档共 {total} 页）"
            entry["text"] = ""
        else:
            page = doc.load_page(idx)
            # 仅该页：get_text 不触发全文档扫描
            entry["text"] = page.get_text("text") or ""
        result["pages"].append(entry)

    doc.close()
    return result


def analyze_question_types(text: str) -> dict[str, Any]:
    """
    根据文本特征粗略归类题目类型（启发式，需结合人工校对）。
    """
    if not text or not text.strip():
        return {"summary": "无文本或为空", "hints": []}

    hints: list[str] = []
    t = text

    # 判断题常见标记
    if re.search(r"正确|错误|√|×|对错|判断", t):
        hints.append("判断题")
    if re.search(r"答案\s*[:：]\s*(正确|错误)", t):
        hints.append("含「答案：正确/错误」形式的判断题")

    # 选择题选项行
    opt_lines = len(re.findall(r"(?m)^\s*[A-Da-d][\.、．\s]", t))
    if opt_lines >= 2:
        hints.append("单选题或多选题（检测到 A/B/C/D 样式选项行）")
    if re.search(r"多选|多项选择|不定项", t):
        hints.append("多选题")

    # 填空
    if re.search(r"_{3,}|填空|____+", t):
        hints.append("填空题")

    # 简答 / 论述
    if re.search(r"简答|论述|简述|分析.*要点", t):
        hints.append("简答或论述题")

    # 去重并保持顺序
    ordered: list[str] = []
    seen: set[str] = set()
    for h in hints:
        if h not in seen:
            seen.add(h)
            ordered.append(h)

    return {
        "summary": "、".join(ordered) if ordered else "未匹配到明确题型关键词，可能为扫描版需 OCR 或版式特殊",
        "hints": ordered,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="按页读取考试 PDF 文本并做题型粗分析")
    parser.add_argument(
        "--pdf",
        type=str,
        default="",
        help="PDF 文件路径（请将《生成式AI工程师（高级）理论模拟题.pdf》放在此路径）",
    )
    parser.add_argument(
        "--pages",
        type=str,
        default=",".join(str(p) for p in DEFAULT_PAGE_NUMBERS_ONE_BASED),
        help="逗号分隔的页码列表，1 起算，例如 2,3,78,150",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="",
        help="可选：将合并文本写入该文件（UTF-8）",
    )
    parser.add_argument(
        "--json",
        type=str,
        default="",
        help="可选：将结构化结果写入该 JSON 文件（UTF-8）",
    )
    args = parser.parse_args()

    if not args.pdf.strip():
        print("请使用 --pdf 指定 PDF 完整路径。", file=sys.stderr)
        sys.exit(2)

    pages_list = [int(x.strip()) for x in args.pages.split(",") if x.strip()]

    data = extract_pages_text(Path(args.pdf), pages_list)

    # 逐页题型分析
    for p in data["pages"]:
        p["question_type_analysis"] = analyze_question_types(p.get("text") or "")

    merged_text_parts: list[str] = []
    for p in data["pages"]:
        merged_text_parts.append(f"\n===== 第 {p['page_one_based']} 页 =====\n")
        merged_text_parts.append(p.get("text") or "")
        merged_text_parts.append(
            f"\n[题型粗判] {p['question_type_analysis'].get('summary', '')}\n"
        )

    merged = "".join(merged_text_parts)
    print(merged)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(merged, encoding="utf-8")
        print(f"已写入: {out_path.resolve()}", file=sys.stderr)

    if args.json:
        json_path = Path(args.json)
        json_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"已写入 JSON: {json_path.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    main()
