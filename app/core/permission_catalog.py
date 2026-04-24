# -*- coding: utf-8 -*-
"""系统全局功能点目录（菜单、列表、表单、字段、操作），供角色授权与前后端校验。

新增业务菜单、接口或按钮时，须在本文件 CATALOG 中追加对应条目（含 code/name/label/kind），
并保证 app.core.permission_catalog.ALL_CODES 与路由 meta.permission 一致，否则授权界面不会出现新功能点。
"""

from typing import Any, Dict, List, Tuple, TypedDict


class CatalogItem(TypedDict):
    code: str
    name: str
    label: str
    kind: str


# kind: menu | list | form | field | action | module
CATALOG: List[CatalogItem] = [
    {"code": "menu.home", "name": "首页", "label": "导航与入口", "kind": "menu"},
    {"code": "menu.exam.qb_center", "name": "题库中心", "label": "考试业务", "kind": "module"},
    {"code": "menu.exam.question_manage", "name": "题库管理", "label": "考试业务", "kind": "menu"},
    {"code": "menu.exam.paper_manage", "name": "试卷管理", "label": "考试业务", "kind": "menu"},
    {"code": "menu.exam.paper_publish", "name": "场次发布", "label": "考试业务", "kind": "menu"},
    {"code": "module.exam.paper_archive", "name": "试卷档案", "label": "考试业务", "kind": "module"},
    {"code": "menu.exam.sessions", "name": "考试场次", "label": "考试业务", "kind": "module"},
    {"code": "menu.exam.available", "name": "在线考试", "label": "考试业务", "kind": "menu"},
    {"code": "menu.exam.candidate_manage", "name": "考生管理", "label": "考试业务", "kind": "menu"},
    {"code": "menu.exam.exam_services", "name": "考试服务", "label": "考试业务", "kind": "menu"},
    {"code": "menu.exam.wrong_practice", "name": "错题练习", "label": "考试业务", "kind": "menu"},
    {"code": "menu.exam.certificate", "name": "证书管理", "label": "考试业务", "kind": "menu"},
    {"code": "module.system", "name": "系统管理", "label": "系统管理", "kind": "module"},
    {"code": "menu.system.user_manage", "name": "用户管理", "label": "系统管理", "kind": "menu"},
    {"code": "menu.system.users", "name": "用户信息", "label": "系统管理-用户", "kind": "menu"},
    {"code": "menu.system.roles", "name": "角色权限", "label": "系统管理-用户", "kind": "menu"},
    {"code": "menu.system.basic", "name": "基础信息", "label": "系统管理", "kind": "menu"},
    {"code": "menu.system.enterprise", "name": "企业信息", "label": "系统管理-基础信息", "kind": "menu"},
    {"code": "menu.system.course", "name": "课程信息", "label": "系统管理-基础信息", "kind": "menu"},
    {"code": "menu.system.paper_level", "name": "试卷等级", "label": "系统管理-基础信息", "kind": "menu"},
    {"code": "menu.system.student", "name": "学员管理", "label": "系统管理-基础信息", "kind": "menu"},
    {"code": "menu.system.settings", "name": "设置中心", "label": "系统管理", "kind": "menu"},
    {"code": "menu.system.document", "name": "单据设计", "label": "系统管理-设置中心", "kind": "menu"},
    {"code": "menu.system.print", "name": "打印设置", "label": "系统管理-设置中心", "kind": "menu"},
    {"code": "list.print_template", "name": "打印模板列表", "label": "系统管理-设置中心", "kind": "list"},
    {"code": "form.print_template", "name": "打印模板表单", "label": "系统管理-设置中心", "kind": "form"},
    {"code": "action.print_template.manage", "name": "打印模板维护", "label": "系统管理-设置中心", "kind": "action"},
    {"code": "menu.system.supervision", "name": "监管服务", "label": "系统管理", "kind": "menu"},
    {"code": "menu.system.online", "name": "在线用户", "label": "系统管理-监管服务", "kind": "menu"},
    {"code": "menu.system.logs", "name": "日志管理", "label": "系统管理-监管服务", "kind": "menu"},
    {"code": "menu.bi", "name": "数智BI中心", "label": "数据分析", "kind": "menu"},
    {"code": "list.question", "name": "题库列表", "label": "题库管理", "kind": "list"},
    {"code": "list.paper", "name": "试卷列表", "label": "试卷管理", "kind": "list"},
    {"code": "list.session", "name": "场次列表", "label": "考试场次", "kind": "list"},
    {"code": "list.user", "name": "用户列表", "label": "用户信息", "kind": "list"},
    {"code": "list.role", "name": "角色列表", "label": "角色权限", "kind": "list"},
    {"code": "list.enterprise", "name": "企业列表", "label": "企业信息", "kind": "list"},
    {"code": "list.course", "name": "课程列表", "label": "课程信息", "kind": "list"},
    {"code": "list.paper_level", "name": "试卷等级列表", "label": "试卷等级", "kind": "list"},
    {"code": "list.attempt", "name": "答卷记录", "label": "列表资源", "kind": "list"},
    {"code": "list.student", "name": "学员列表", "label": "学员管理", "kind": "list"},
    {"code": "list.exam_candidate", "name": "考生列表", "label": "考生管理", "kind": "list"},
    {"code": "list.exam_service_record", "name": "考试服务记录", "label": "考试服务", "kind": "list"},
    {"code": "list.wrong_practice", "name": "错题练习列表", "label": "错题练习", "kind": "list"},
    {"code": "list.cert_template", "name": "证书模板列表", "label": "证书管理", "kind": "list"},
    {"code": "list.cert_record", "name": "证书颁发记录", "label": "证书管理", "kind": "list"},
    {"code": "form.user", "name": "用户表单", "label": "用户信息", "kind": "form"},
    {"code": "form.enterprise", "name": "企业表单", "label": "企业信息", "kind": "form"},
    {"code": "form.role", "name": "角色表单", "label": "角色权限", "kind": "form"},
    {"code": "form.course", "name": "课程表单", "label": "课程信息", "kind": "form"},
    {"code": "form.question", "name": "题库新建表单", "label": "题库管理", "kind": "form"},
    {"code": "form.question_import", "name": "导入题库", "label": "题库管理", "kind": "form"},
    {"code": "form.question_batch", "name": "题库批量操作", "label": "题库管理", "kind": "form"},
    {"code": "form.paper", "name": "试卷新建表单", "label": "试卷管理", "kind": "form"},
    {"code": "form.session", "name": "场次新建表单", "label": "考试场次", "kind": "form"},
    {"code": "form.student", "name": "学员表单", "label": "学员管理", "kind": "form"},
    {"code": "form.exam_candidate", "name": "考生表单", "label": "考生管理", "kind": "form"},
    {"code": "form.cert_template", "name": "证书模板表单", "label": "证书管理", "kind": "form"},
    {"code": "field.user.username", "name": "用户名", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.password", "name": "密码", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.full_name", "name": "姓名", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.role", "name": "角色", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.enterprise", "name": "所属企业", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.is_active", "name": "启用", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.student", "name": "关联学员", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.enable_date", "name": "启用日期", "label": "字段-用户", "kind": "field"},
    {"code": "field.user.expire_date", "name": "失效日期", "label": "字段-用户", "kind": "field"},
    {"code": "field.enterprise.license", "name": "营业执照附件", "label": "字段-企业", "kind": "field"},
    {"code": "field.enterprise.tax_id", "name": "纳税人识别号", "label": "字段-企业", "kind": "field"},
    {"code": "field.course.name", "name": "课程名称", "label": "字段-课程", "kind": "field"},
    {"code": "field.course.instructor", "name": "讲师", "label": "字段-课程", "kind": "field"},
    {"code": "field.course.period", "name": "课程期间", "label": "字段-课程", "kind": "field"},
    {"code": "field.course.description", "name": "课程简介", "label": "字段-课程", "kind": "field"},
    {"code": "field.course.enterprise", "name": "所属企业", "label": "字段-课程", "kind": "field"},
    {"code": "field.question.question_no", "name": "题号", "label": "字段-题库", "kind": "field"},
    {"code": "field.question.q_type", "name": "题型", "label": "字段-题库", "kind": "field"},
    {"code": "field.question.stem", "name": "题干", "label": "字段-题库", "kind": "field"},
    {"code": "field.question.options_json", "name": "选项", "label": "字段-题库", "kind": "field"},
    {"code": "field.question.answer_json", "name": "答案", "label": "字段-题库", "kind": "field"},
    {"code": "field.question.analysis", "name": "解析", "label": "字段-题库", "kind": "field"},
    {"code": "field.question.difficulty", "name": "难度", "label": "字段-题库", "kind": "field"},
    {"code": "field.question.status", "name": "状态", "label": "字段-题库", "kind": "field"},
    {"code": "field.question.course_id", "name": "课程", "label": "字段-题库", "kind": "field"},
    {"code": "field.question.enterprise_id", "name": "所属企业", "label": "字段-题库", "kind": "field"},
    {"code": "field.paper.title", "name": "试卷名称", "label": "字段-试卷", "kind": "field"},
    {"code": "field.paper.paper_no", "name": "试卷编号", "label": "字段-试卷", "kind": "field"},
    {"code": "field.paper.course_id", "name": "课程", "label": "字段-试卷", "kind": "field"},
    {"code": "field.paper.paper_type", "name": "试卷类型", "label": "字段-试卷", "kind": "field"},
    {"code": "field.paper.level_id", "name": "试卷等级", "label": "字段-试卷", "kind": "field"},
    {"code": "field.paper.description", "name": "说明", "label": "字段-试卷", "kind": "field"},
    {"code": "field.paper.duration_minutes", "name": "时长(分钟)", "label": "字段-试卷", "kind": "field"},
    {"code": "field.paper.pass_rate", "name": "及格率", "label": "字段-试卷", "kind": "field"},
    {"code": "field.paper.pass_score", "name": "及格分", "label": "字段-试卷", "kind": "field"},
    {"code": "field.paper.rules", "name": "组卷规则", "label": "字段-试卷", "kind": "field"},
    {"code": "field.student.student_no", "name": "学员编号", "label": "字段-学员", "kind": "field"},
    {"code": "field.student.full_name", "name": "姓名", "label": "字段-学员", "kind": "field"},
    {"code": "field.student.gender", "name": "性别", "label": "字段-学员", "kind": "field"},
    {"code": "field.student.birth_month", "name": "出生年月", "label": "字段-学员", "kind": "field"},
    {"code": "field.student.phone", "name": "联系电话", "label": "字段-学员", "kind": "field"},
    {"code": "field.student.id_card_no", "name": "身份证号", "label": "字段-学员", "kind": "field"},
    {"code": "field.student.address_phone", "name": "地址电话", "label": "字段-学员", "kind": "field"},
    {"code": "field.student.remark", "name": "备注", "label": "字段-学员", "kind": "field"},
    {"code": "field.student.enterprise_id", "name": "所属企业", "label": "字段-学员", "kind": "field"},
    {"code": "field.exam_candidate.exam_no", "name": "考试编号", "label": "字段-考生", "kind": "field"},
    {"code": "field.exam_candidate.enterprise_id", "name": "所属企业", "label": "字段-考生", "kind": "field"},
    {"code": "field.exam_candidate.course_id", "name": "课程", "label": "字段-考生", "kind": "field"},
    {"code": "field.exam_candidate.student_id", "name": "学员", "label": "字段-考生", "kind": "field"},
    {"code": "field.exam_candidate.created_at", "name": "创建时间", "label": "字段-考生", "kind": "field"},
    {"code": "field.exam_candidate.session_id", "name": "场次", "label": "字段-考生", "kind": "field"},
    {"code": "field.exam_candidate.last_attempt_id", "name": "最近作答", "label": "字段-考生", "kind": "field"},
    {"code": "field.exam_candidate.answer_duration_seconds", "name": "作答时长", "label": "字段-考生", "kind": "field"},
    {"code": "field.exam_service_record.exam_no", "name": "考试编号", "label": "字段-考试服务", "kind": "field"},
    {"code": "field.exam_service_record.course_name", "name": "课程名称", "label": "字段-考试服务", "kind": "field"},
    {"code": "field.exam_service_record.paper_title", "name": "试卷名称", "label": "字段-考试服务", "kind": "field"},
    {"code": "field.exam_service_record.enterprise_name", "name": "所属企业", "label": "字段-考试服务", "kind": "field"},
    {"code": "field.exam_service_record.student_display", "name": "学员", "label": "字段-考试服务", "kind": "field"},
    {"code": "field.exam_service_record.score", "name": "得分", "label": "字段-考试服务", "kind": "field"},
    {"code": "field.exam_service_record.passed", "name": "是否通过", "label": "字段-考试服务", "kind": "field"},
    {"code": "field.exam_service_record.created_at", "name": "记录时间", "label": "字段-考试服务", "kind": "field"},
    {"code": "field.wrong_practice.course_name", "name": "课程名称", "label": "字段-错题练习", "kind": "field"},
    {"code": "field.wrong_practice.enterprise_name", "name": "所属企业", "label": "字段-错题练习", "kind": "field"},
    {"code": "field.wrong_practice.wrong_count", "name": "错题数", "label": "字段-错题练习", "kind": "field"},
    {"code": "action.wrong_practice.enter", "name": "进入练习", "label": "错题练习", "kind": "action"},
    {"code": "field.session.paper_id", "name": "试卷", "label": "字段-场次", "kind": "field"},
    {"code": "field.session.title", "name": "场次名称", "label": "字段-场次", "kind": "field"},
    {"code": "field.session.start_at", "name": "开始时间", "label": "字段-场次", "kind": "field"},
    {"code": "field.session.end_at", "name": "结束时间", "label": "字段-场次", "kind": "field"},
    {"code": "field.session.status", "name": "状态", "label": "字段-场次", "kind": "field"},
    {"code": "action.user.create", "name": "新建用户", "label": "用户信息", "kind": "action"},
    {"code": "action.user.update", "name": "编辑用户", "label": "用户信息", "kind": "action"},
    {"code": "action.user.delete", "name": "删除用户", "label": "用户信息", "kind": "action"},
    {"code": "action.user.import", "name": "导入用户", "label": "用户信息", "kind": "action"},
    {"code": "action.role.create", "name": "新建角色", "label": "角色权限", "kind": "action"},
    {"code": "action.role.update", "name": "编辑角色", "label": "角色权限", "kind": "action"},
    {"code": "action.role.delete", "name": "删除角色", "label": "角色权限", "kind": "action"},
    {"code": "action.role.permission", "name": "角色功能授权", "label": "角色权限", "kind": "action"},
    {"code": "action.enterprise.create", "name": "新建企业", "label": "企业信息", "kind": "action"},
    {"code": "action.enterprise.update", "name": "编辑企业", "label": "企业信息", "kind": "action"},
    {"code": "action.enterprise.delete", "name": "删除企业", "label": "企业信息", "kind": "action"},
    {"code": "action.course.create", "name": "新建课程", "label": "课程信息", "kind": "action"},
    {"code": "action.course.update", "name": "编辑课程", "label": "课程信息", "kind": "action"},
    {"code": "action.course.delete", "name": "删除课程", "label": "课程信息", "kind": "action"},
    {"code": "action.paper_level.manage", "name": "试卷等级维护", "label": "试卷等级", "kind": "action"},
    {"code": "action.question.manage", "name": "题目维护", "label": "题库管理", "kind": "action"},
    {"code": "action.question.import", "name": "导入题库", "label": "题库管理", "kind": "action"},
    {"code": "action.question.batch", "name": "题库批量操作", "label": "题库管理", "kind": "action"},
    {"code": "action.paper.manage", "name": "试卷维护", "label": "试卷管理", "kind": "action"},
    {"code": "action.session.manage", "name": "场次维护", "label": "考试场次", "kind": "action"},
    {"code": "action.exam_candidate.create", "name": "新建考生", "label": "考生管理", "kind": "action"},
    {"code": "action.exam_candidate.update", "name": "编辑考生", "label": "考生管理", "kind": "action"},
    {"code": "action.exam_candidate.delete", "name": "删除考生", "label": "考生管理", "kind": "action"},
    {"code": "action.exam.take", "name": "在线考试作答", "label": "考试管理", "kind": "action"},
    {"code": "action.cert_template.manage", "name": "证书模板维护", "label": "证书管理", "kind": "action"},
    {"code": "action.cert_record.issue", "name": "颁发证书", "label": "证书管理", "kind": "action"},
    {"code": "action.student.create", "name": "新建学员", "label": "学员管理", "kind": "action"},
    {"code": "action.student.update", "name": "编辑学员", "label": "学员管理", "kind": "action"},
    {"code": "action.student.delete", "name": "删除学员", "label": "学员管理", "kind": "action"},
    {"code": "action.student.import", "name": "导入学员信息", "label": "学员管理", "kind": "action"},
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


# 功能点 code -> (module_key, module_title)，前缀自左向右优先匹配
_MODULE_RULES: List[Tuple[str, str, str]] = [
    ("menu.home", "nav", "导航与入口"),
    ("menu.exam.qb_center", "qb_center", "题库中心"),
    ("menu.exam.question_manage", "qb_center", "题库中心"),
    ("list.question", "qb_center", "题库中心"),
    ("form.question", "qb_center", "题库中心"),
    ("form.question_import", "qb_center", "题库中心"),
    ("form.question_batch", "qb_center", "题库中心"),
    ("field.question.", "qb_center", "题库中心"),
    ("action.question.", "qb_center", "题库中心"),
    ("module.exam.paper_archive", "paper_archive", "试卷档案"),
    ("menu.exam.paper_manage", "paper_archive", "试卷档案"),
    ("menu.exam.paper_publish", "paper_archive", "试卷档案"),
    ("list.paper", "paper_archive", "试卷档案"),
    ("form.paper", "paper_archive", "试卷档案"),
    ("field.paper.", "paper_archive", "试卷档案"),
    ("action.paper.", "paper_archive", "试卷档案"),
    ("menu.exam.sessions", "sessions", "考试场次"),
    ("list.session", "sessions", "考试场次"),
    ("form.session", "sessions", "考试场次"),
    ("field.session.", "sessions", "考试场次"),
    ("action.session.", "sessions", "考试场次"),
    ("menu.exam.available", "exam_manage", "考试管理"),
    ("menu.exam.candidate_manage", "exam_manage", "考试管理"),
    ("menu.exam.exam_services", "exam_manage", "考试管理"),
    ("menu.exam.wrong_practice", "exam_manage", "考试管理"),
    ("list.attempt", "exam_manage", "考试管理"),
    ("action.exam.", "exam_manage", "考试管理"),
    ("list.exam_candidate", "exam_manage", "考试管理"),
    ("form.exam_candidate", "exam_manage", "考试管理"),
    ("field.exam_candidate.", "exam_manage", "考试管理"),
    ("action.exam_candidate.", "exam_manage", "考试管理"),
    ("list.exam_service_record", "exam_manage", "考试管理"),
    ("field.exam_service_record.", "exam_manage", "考试管理"),
    ("list.wrong_practice", "exam_manage", "考试管理"),
    ("field.wrong_practice.", "exam_manage", "考试管理"),
    ("action.wrong_practice.", "exam_manage", "考试管理"),
    ("menu.exam.", "exam", "考试业务"),
    ("module.system", "sys", "系统管理"),
    ("menu.system.", "sys", "系统管理"),
    ("menu.bi", "data_bi", "数据分析"),
    ("list.question", "exam", "考试业务"),
    ("list.paper", "exam", "考试业务"),
    ("list.session", "exam", "考试业务"),
    ("list.user", "sys", "系统管理"),
    ("list.role", "sys", "系统管理"),
    ("list.enterprise", "sys", "系统管理"),
    ("list.course", "sys", "系统管理"),
    ("list.paper_level", "sys", "系统管理"),
    ("list.print_template", "sys", "系统管理"),
    ("list.student", "sys", "系统管理"),
    ("form.user", "sys", "系统管理"),
    ("form.role", "sys", "系统管理"),
    ("form.enterprise", "sys", "系统管理"),
    ("form.course", "sys", "系统管理"),
    ("form.student", "sys", "系统管理"),
    ("form.print_template", "sys", "系统管理"),
    ("field.user.", "sys", "系统管理"),
    ("field.enterprise.", "sys", "系统管理"),
    ("field.course.", "sys", "系统管理"),
    ("field.student.", "sys", "系统管理"),
    ("action.user.", "sys", "系统管理"),
    ("action.role.", "sys", "系统管理"),
    ("action.enterprise.", "sys", "系统管理"),
    ("action.course.", "sys", "系统管理"),
    ("action.paper_level.", "sys", "系统管理"),
    ("action.student.", "sys", "系统管理"),
    ("action.print_template.", "sys", "系统管理"),
]

_FUNCTION_MODULE_ORDER = (
    "nav",
    "qb_center",
    "paper_archive",
    "sessions",
    "exam_manage",
    "exam",
    "sys",
    "data_bi",
    "other",
)


def _module_for_code(code: str) -> Tuple[str, str]:
    for prefix, mk, mt in _MODULE_RULES:
        if code == prefix or code.startswith(prefix):
            return (mk, mt)
    return ("other", "其他")


def _entity_from_list_or_form(code: str) -> str | None:
    parts = code.split(".")
    if len(parts) >= 2 and parts[0] in ("list", "form"):
        ent = parts[1]
        # 题库导入/批量操作沿用题库字段授权
        if ent in ("question_import", "question_batch"):
            return "question"
        return ent
    return None


def _fields_for_entity(entity: str) -> List[CatalogItem]:
    prefix = f"field.{entity}."
    return [it for it in CATALOG if it.get("kind") == "field" and it["code"].startswith(prefix)]


def catalog_function_module_tree() -> List[Dict[str, Any]]:
    """按功能模块聚合：每模块下菜单、列表/表单及其所含字段树，另附操作点。"""
    buckets: Dict[str, Dict[str, Any]] = {}

    for it in CATALOG:
        kind = it.get("kind")
        if kind == "field":
            continue
        if kind not in ("menu", "list", "form", "action", "module"):
            continue
        mk, mt = _module_for_code(it["code"])
        if mk not in buckets:
            buckets[mk] = {
                "moduleKey": mk,
                "moduleTitle": mt,
                "moduleCode": None,
                "menus": [],
                "lists": [],
                "forms": [],
                "actions": [],
            }
        if kind == "module":
            # 系统模块节点：用于授权树展示为模块标题，不计入菜单/列表/表单/操作
            buckets[mk]["moduleCode"] = it["code"]
            continue
        if kind == "menu":
            buckets[mk]["menus"].append(it)
        elif kind == "list":
            ent = _entity_from_list_or_form(it["code"])
            flist = _fields_for_entity(ent) if ent else []
            buckets[mk]["lists"].append({"item": it, "fields": flist})
        elif kind == "form":
            ent = _entity_from_list_or_form(it["code"])
            flist = _fields_for_entity(ent) if ent else []
            buckets[mk]["forms"].append({"item": it, "fields": flist})
        elif kind == "action":
            buckets[mk]["actions"].append(it)

    def _sort_key(mk: str) -> int:
        try:
            return _FUNCTION_MODULE_ORDER.index(mk)
        except ValueError:
            return len(_FUNCTION_MODULE_ORDER)

    return [buckets[k] for k in sorted(buckets.keys(), key=_sort_key)]
