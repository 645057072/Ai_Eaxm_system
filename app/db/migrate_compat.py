# -*- coding: utf-8 -*-
"""Alembic 迁移兼容工具（幂等执行）。

用于兼容以下场景：
- 挂载已有数据库（表/字段/索引/外键已存在，但 alembic_version 未同步）
- 历史迁移中断后重复执行
- 手工改库导致 schema 与迁移脚本不完全一致

注意：这里只做“是否存在”的探测，具体约束差异（如字段类型不一致）不在本工具范围内。
"""

from __future__ import annotations

from typing import Any

from alembic import op
from sqlalchemy import inspect


def _insp():
    bind = op.get_bind()
    return inspect(bind)


def has_table(table: str) -> bool:
    insp = _insp()
    try:
        return bool(insp.has_table(table))
    except Exception:
        try:
            return table in (insp.get_table_names() or [])
        except Exception:
            return False


def has_column(table: str, col: str) -> bool:
    insp = _insp()
    try:
        cols = insp.get_columns(table) or []
        return any((c.get("name") == col) for c in cols)
    except Exception:
        return False


def has_index(table: str, index_name: str) -> bool:
    insp = _insp()
    try:
        idx = insp.get_indexes(table) or []
        return any((i.get("name") == index_name) for i in idx)
    except Exception:
        return False


def has_fk(table: str, fk_name: str) -> bool:
    insp = _insp()
    try:
        fks = insp.get_foreign_keys(table) or []
        return any((fk.get("name") == fk_name) for fk in fks)
    except Exception:
        return False


def has_unique(table: str, uq_name: str) -> bool:
    """MySQL 下 unique 可能表现为 unique_constraints 或 unique 索引，两种都探测。"""
    insp = _insp()
    try:
        uqs = insp.get_unique_constraints(table) or []
        if any((u.get("name") == uq_name) for u in uqs):
            return True
    except Exception:
        pass
    try:
        idx = insp.get_indexes(table) or []
        return any((i.get("name") == uq_name and i.get("unique")) for i in idx)
    except Exception:
        return False


def safe_create_index(name: str, table: str, columns: list[str], unique: bool = False, **kw: Any) -> None:
    if has_index(table, name):
        return
    try:
        op.create_index(name, table, columns, unique=unique, **kw)
    except Exception:
        # 兼容：并发/历史残留导致重复创建
        pass


def safe_create_fk(
    name: str,
    source_table: str,
    referent_table: str,
    local_cols: list[str],
    remote_cols: list[str],
    **kw: Any,
) -> None:
    if has_fk(source_table, name):
        return
    try:
        op.create_foreign_key(name, source_table, referent_table, local_cols, remote_cols, **kw)
    except Exception:
        pass

