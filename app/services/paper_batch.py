# -*- coding: utf-8 -*-
"""按题型总量均分到多套试卷并无放回抽题。"""

import random
from decimal import Decimal
from typing import Dict, List, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.paper_compose import fetch_question_pool_ids


def split_total_across_papers(total: int, paper_count: int) -> List[int]:
    """将 total 拆成 paper_count 份非负整数，尽量均匀（余数摊到前若干套）。"""
    if paper_count < 1:
        raise HTTPException(status_code=400, detail="生成试卷份数至少为 1")
    if total < 0:
        raise HTTPException(status_code=400, detail="题型总量不能为负")
    if total == 0:
        return [0] * paper_count
    base = total // paper_count
    rem = total % paper_count
    return [base + (1 if i < rem else 0) for i in range(paper_count)]


def build_disjoint_chunks_for_type(
    db: Session,
    *,
    course_id: int,
    enterprise_id: int,
    q_type: str,
    total: int,
    paper_count: int,
) -> List[List[int]]:
    """某题型从题库抽取 total 题，按套数切成互不重叠的列表。"""
    if total <= 0:
        return [[] for _ in range(paper_count)]
    pool = fetch_question_pool_ids(db, course_id=course_id, enterprise_id=enterprise_id, q_type=q_type)
    if len(pool) < total:
        raise HTTPException(
            status_code=400,
            detail=f"题型 {q_type} 可用题目 {len(pool)} 道，少于该题型总量 {total}",
        )
    random.shuffle(pool)
    chosen = pool[:total]
    sizes = split_total_across_papers(total, paper_count)
    chunks: List[List[int]] = []
    offset = 0
    for s in sizes:
        chunks.append(chosen[offset : offset + s])
        offset += s
    return chunks


def merge_items_in_rule_order(
    type_chunks: Dict[str, List[List[int]]],
    rule_order: List[str],
    paper_count: int,
    score_per: Decimal,
    auto_split: int,
) -> List[List[Tuple[int, Decimal, int]]]:
    """按 rule_order 合并各题型，得到每套试卷的 (question_id, score, auto_split) 列表。"""
    per_paper: List[List[Tuple[int, Decimal, int]]] = [[] for _ in range(paper_count)]
    for pi in range(paper_count):
        for qt in rule_order:
            if qt not in type_chunks:
                continue
            for qid in type_chunks[qt][pi]:
                per_paper[pi].append((qid, score_per, auto_split))
    return per_paper
