# -*- coding: utf-8 -*-
"""练习卷交卷报告：得分统计 + 已作答错题逐条分析（未答题不写入）。"""

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
) -> str:
    """生成结构化报告：仅列出已作答且不得满分的题目，全文不截断。"""
    if full_score <= 0:
        full_score = Decimal("1")
    rate = (earned / full_score * Decimal("100")).quantize(Decimal("0.1"))
    n_all = len(rows)
    n_ok = sum(1 for r in rows if r.get("full_correct"))
    n_answered = sum(1 for r in rows if r.get("answered"))
    n_blank = n_all - n_answered
    wrong_answered = [r for r in rows if r.get("answered") and not r.get("full_correct")]

    lines: list[str] = []
    lines.append("【练习答卷报告】")
    lines.append(f"场次：{session_title}")
    lines.append(f"试卷：{paper_title}")
    lines.append(f"得分：{earned} / {full_score}（得分率约 {rate}%）")
    lines.append(
        f"全对题数：{n_ok}，已作答错题数：{len(wrong_answered)}，未答题数：{n_blank}"
        f"（未作答题目不列入下文分析）。"
    )
    lines.append("")
    lines.append("【错题要点】（仅含已作答且不得满分的题目）")
    if not wrong_answered:
        lines.append("无已作答错题；未作答题目不列入本报告。")
    else:
        for r in wrong_answered:
            idx = r.get("index", 0)
            ql = r.get("type_label") or ""
            stem = (r.get("stem") or r.get("stem_preview") or "").strip()
            know = (r.get("knowledge") or "").strip()
            if know:
                lines.append(f"{idx}. [{ql}] {stem} 知识点：{know}")
            else:
                lines.append(f"{idx}. [{ql}] {stem}")
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
        "请针对上述错题对照题库解析与教材相关章节逐题订正；"
        "判断与单选重在概念辨析，多选注意漏选，填空注意表述规范。"
    )
    lines.append("")
    lines.append("【学习计划】")
    lines.append(
        "建议每日安排固定时段复盘错题与解析，结合课程进度分模块巩固；"
        "一周内完成同类题型二次练习，并记录仍易错点以便专项突破。"
    )

    return "\n".join(lines)
