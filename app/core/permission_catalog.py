# -*- coding: utf-8 -*-
"""系统全局功能点目录（菜单、列表、表单、字段、操作），供角色授权与前后端校验。

新增业务菜单、接口或按钮时，须在本文件 CATALOG 中追加对应条目（含 code/name/label/kind），
并保证 app.core.permission_catalog.ALL_CODES 与路由 meta.permission 一致，否则授权界面不会出现新功能点。
"""

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


# kind 展示顺序与中文标题（授权弹窗按层级：菜单 / 列表 / 表单 / 字段 / 操作）
_KIND_ORDER = ("menu", "list", "form", "field", "action")
_KIND_TITLE: dict[str, str] = {
    "menu": "菜单",
    "list": "列表",
    "form": "表单",
    "field": "字段",
    "action": "操作",
}


def catalog_by_kind_sections() -> List[dict[str, Any]]:
    """按 kind 再按业务标签（label）分组，供前端弹窗分层勾选。"""
    label_order: dict[str, List[str]] = {k: [] for k in _KIND_ORDER}
    buckets: dict[str, dict[str, List[CatalogItem]]] = {k: {} for k in _KIND_ORDER}
    for it in CATALOG:
        k = it.get("kind")
        if k not in buckets:
            continue
        lb = it["label"]
        if lb not in buckets[k]:
            buckets[k][lb] = []
            label_order[k].append(lb)
        buckets[k][lb].append(it)
    out: List[dict[str, Any]] = []
    for k in _KIND_ORDER:
        if not label_order[k]:
            continue
        sections = [{"label": lb, "items": buckets[k][lb]} for lb in label_order[k]]
        out.append({"kind": k, "title": _KIND_TITLE.get(k, k), "sections": sections})
    return out


def _split_label(lb: str) -> tuple[str, str]:
    """label 形如「系统管理-用户」拆成模块与分组；无连字符则分组为「默认」。"""
    if "-" in lb:
        a, b = lb.split("-", 1)
        return a.strip(), b.strip()
    return lb.strip(), "默认"


def catalog_mlf_tree() -> List[dict[str, Any]]:
    """模块 -> 业务分组 -> 菜单/列表/表单 树形结构（不含字段与操作）。"""
    module_order: List[str] = []
    modules: dict[str, dict[str, Any]] = {}
    for it in CATALOG:
        k = it.get("kind")
        if k not in ("menu", "list", "form"):
            continue
        mod, grp = _split_label(it["label"])
        if mod not in modules:
            module_order.append(mod)
            modules[mod] = {"groupOrder": [], "groups": {}}
        m = modules[mod]
        if grp not in m["groups"]:
            m["groupOrder"].append(grp)
            m["groups"][grp] = {"menus": [], "lists": [], "forms": []}
        key = {"menu": "menus", "list": "lists", "form": "forms"}[k]
        m["groups"][grp][key].append(it)
    result: List[dict[str, Any]] = []
    for mod in module_order:
        groups_out: List[dict[str, Any]] = []
        for grp in modules[mod]["groupOrder"]:
            g = modules[mod]["groups"][grp]
            groups_out.append(
                {
                    "name": grp,
                    "menus": g["menus"],
                    "lists": g["lists"],
                    "forms": g["forms"],
                }
            )
        result.append({"module": mod, "groups": groups_out})
    return result


def catalog_field_tag_groups() -> List[dict[str, Any]]:
    """字段类功能点按 label 分组，供横向标签勾选。"""
    order: List[str] = []
    buckets: dict[str, List[CatalogItem]] = {}
    for it in CATALOG:
        if it.get("kind") != "field":
            continue
        lb = it["label"]
        if lb not in buckets:
            buckets[lb] = []
            order.append(lb)
        buckets[lb].append(it)
    return [{"label": lb, "items": buckets[lb]} for lb in order]


def catalog_action_groups() -> List[dict[str, Any]]:
    """操作类功能点按 label 分组。"""
    order: List[str] = []
    buckets: dict[str, List[CatalogItem]] = {}
    for it in CATALOG:
        if it.get("kind") != "action":
            continue
        lb = it["label"]
        if lb not in buckets:
            buckets[lb] = []
            order.append(lb)
        buckets[lb].append(it)
    return [{"label": lb, "items": buckets[lb]} for lb in order]
