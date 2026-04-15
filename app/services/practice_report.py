# -*- coding: utf-8 -*-
"""练习卷交卷报告：基于得分与题目解析生成简短文字（控制在一页A4、宋体五号量级）。"""

from decimal import Decimal
from typing import Any, List


def q_type_label_cn(q_type: str) -> str:
    return {
        "judge": "判断题",
        "single": "单选题",
        "multiple": "多选题",
        "fill": "填空题",
    }.get((q_type or "").strip(), q_type or "题目")


def build_practice_report(
    session_title: str,
    paper_title: str,
    earned: Decimal,
    full_score: Decimal,
    rows: List[dict[str, Any]],
    max_chars: int = 560,
) -> str:
    """生成结构化报告文本，超长截断。"""
    if full_score <= 0:
        full_score = Decimal("1")
    rate = (earned / full_score * Decimal("100")).quantize(Decimal("0.1"))
    n_ok = sum(1 for r in rows if r.get("full_correct"))
    n_all = len(rows) or 1
    n_wrong = n_all - n_ok

    lines: list[str] = []
    lines.append("【练习答卷报告】")
    lines.append(f"场次：{session_title}")
    lines.append(f"试卷：{paper_title}")
    lines.append(f"得分：{earned} / {full_score}（得分率约 {rate}%）")
    lines.append(f"全对题数：{n_ok}，未得满分题数：{n_wrong}。")
    lines.append("")
    lines.append("【逐题要点】")
    for r in rows:
        idx = r.get("index", 0)
        ql = r.get("type_label") or ""
        stem = (r.get("stem_preview", "") or "").strip()
        ok = r.get("full_correct")
        flag = "正确" if ok else "未得满分"
        know = (r.get("knowledge", "") or "").strip()
        if know:
            lines.append(f"{idx}. [{ql}] {stem} … 结果：{flag}。知识点：{know}")
        else:
            lines.append(f"{idx}. [{ql}] {stem} … 结果：{flag}。")
    lines.append("")
    if rate >= Decimal("85"):
        summ = "总体掌握较好，概念与操作要点多数能准确作答。"
        eval_ = "对题库对应知识点理解较扎实，可进入更高强度综合训练。"
    elif rate >= Decimal("60"):
        summ = "整体达到基本掌握水平，部分题型或细节仍有遗漏。"
        eval_ = "已具备一定基础，薄弱环节主要集中在错题涉及的知识点上。"
    else:
        summ = "本次练习得分偏低，建议回到课程与题库夯实基础后再练。"
        eval_ = "需加强对题干涉及概念的理解与记忆，避免凭感觉作答。"

    lines.append("【总结】")
    lines.append(summ)
    lines.append("")
    lines.append("【评价】")
    lines.append(eval_)
    lines.append("")
    lines.append("【改进建议】")
    lines.append(
        "针对未得满分题目，请对照题库解析与教材相关章节逐题订正；"
        "判断与单选重在概念辨析，多选注意漏选，填空注意表述规范。"
    )
    lines.append("")
    lines.append("【学习计划】")
    lines.append(
        "建议每日安排固定时段复盘错题与解析，结合课程进度分模块巩固；"
        "一周内完成同类题型二次练习，并记录仍易错点以便专项突破。"
    )

    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[: max_chars - 6].rstrip() + "\n……（已截断至约一页篇幅）"
    return text
