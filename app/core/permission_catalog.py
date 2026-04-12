# -*- coding: utf-8 -*-
"""系统全局功能点目录（菜单、列表、表单、字段、操作），供角色授权与前后端校验。"""

from typing import Any, List, TypedDict


class CatalogItem(TypedDict):
    code: str
    name: str
    label: str
    kind: str


# kind: menu | list | form | field | action
CATALOG: List[CatalogItem] = [
    {"code": "menu.home", "name": "首页", "label": "导航与入口", "kind": "menu"},
    {"code": "menu.exam.questions", "name": "题库", "label": "考试业务", "kind": "menu"},
    {"code": "menu.exam.papers", "name": "试卷", "label": "考试业务", "kind": "menu"},
    {"code": "menu.exam.sessions", "name": "考试场次", "label": "考试业务", "kind": "menu"},
    {"code": "menu.exam.available", "name": "可参加的考试", "label": "考试业务", "kind": "menu"},
    {"code": "menu.system.users", "name": "用户信息", "label": "系统管理-用户", "kind": "menu"},
    {"code": "menu.system.roles", "name": "角色权限", "label": "系统管理-用户", "kind": "menu"},
    {"code": "menu.system.enterprise", "name": "企业信息", "label": "系统管理-基础信息", "kind": "menu"},
    {"code": "menu.system.course", "name": "课程信息", "label": "系统管理-基础信息", "kind": "menu"},
    {"code": "menu.system.document", "name": "单据设计", "label": "系统管理-设置中心", "kind": "menu"},
    {"code": "menu.system.print", "name": "打印设置", "label": "系统管理-设置中心", "kind": "menu"},
    {"code": "menu.system.online", "name": "在线用户", "label": "系统管理-监管服务", "kind": "menu"},
    {"code": "menu.system.logs", "name": "日志管理", "label": "系统管理-监管服务", "kind": "menu"},
    {"code": "menu.bi", "name": "数智BI中心", "label": "数据分析", "kind": "menu"},
    {"code": "list.question", "name": "题目列表", "label": "列表资源", "kind": "list"},
    {"code": "list.paper", "name": "试卷列表", "label": "列表资源", "kind": "list"},
    {"code": "list.session", "name": "场次列表", "label": "列表资源", "kind": "list"},
    {"code": "list.user", "name": "用户列表", "label": "列表资源", "kind": "list"},
    {"code": "list.role", "name": "角色列表", "label": "列表资源", "kind": "list"},
    {"code": "list.enterprise", "name": "企业列表", "label": "列表资源", "kind": "list"},
    {"code": "list.attempt", "name": "答卷记录", "label": "列表资源", "kind": "list"},
    {"code": "form.user", "name": "用户表单", "label": "表单", "kind": "form"},
    {"code": "form.enterprise", "name": "企业表单", "label": "表单", "kind": "form"},
    {"code": "form.role", "name": "角色表单", "label": "表单", "kind": "form"},
    {"code": "field.user.username", "name": "用户名", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.password", "name": "密码", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.full_name", "name": "姓名", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.role", "name": "角色", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.enterprise", "name": "所属企业", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.is_active", "name": "启用", "label": "字段-用户", "kind": "field"},
    {"code": "field.enterprise.license", "name": "营业执照附件", "label": "字段-企业", "kind": "field"},
    {"code": "field.enterprise.tax_id", "name": "纳税人识别号", "label": "字段-企业", "kind": "field"},
    {"code": "action.user.create", "name": "新建用户", "label": "操作", "kind": "action"},
    {"code": "action.user.update", "name": "编辑用户", "label": "操作", "kind": "action"},
    {"code": "action.user.delete", "name": "删除用户", "label": "操作", "kind": "action"},
    {"code": "action.role.create", "name": "新建角色", "label": "操作", "kind": "action"},
    {"code": "action.role.update", "name": "编辑角色", "label": "操作", "kind": "action"},
    {"code": "action.role.delete", "name": "删除角色", "label": "操作", "kind": "action"},
    {"code": "action.role.permission", "name": "角色功能授权", "label": "操作", "kind": "action"},
    {"code": "action.enterprise.create", "name": "新建企业", "label": "操作", "kind": "action"},
    {"code": "action.enterprise.update", "name": "编辑企业", "label": "操作", "kind": "action"},
    {"code": "action.enterprise.delete", "name": "删除企业", "label": "操作", "kind": "action"},
    {"code": "action.question.manage", "name": "题目维护", "label": "操作", "kind": "action"},
    {"code": "action.paper.manage", "name": "试卷维护", "label": "操作", "kind": "action"},
    {"code": "action.session.manage", "name": "场次维护", "label": "操作", "kind": "action"},
    {"code": "action.exam.take", "name": "在线考试作答", "label": "操作", "kind": "action"},
]

ALL_CODES: List[str] = [x["code"] for x in CATALOG]


def catalog_groups() -> List[dict[str, Any]]:
    """按 label 分组，供前端授权树展示。"""
    order: List[str] = []
    buckets: dict[str, List[CatalogItem]] = {}
    for it in CATALOG:
        lb = it["label"]
        if lb not in buckets:
            buckets[lb] = []
            order.append(lb)
        buckets[lb].append(it)
    return [{"label": lb, "items": buckets[lb]} for lb in order]
