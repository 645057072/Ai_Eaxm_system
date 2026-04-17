<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title">场次发布：维护考试场次并发布</div>
      </template>
      <div class="page-list-toolbar toolbar">
        <el-button type="success" @click="openCreate">新建场次</el-button>
        <el-input
          v-model="filterTitleKw"
          clearable
          placeholder="试卷标题/场次标题"
          style="width: 200px"
          @keyup.enter="doSearch"
        />
        <el-button type="primary" @click="doSearch">查询</el-button>
        <el-dropdown v-if="canManage" trigger="click" @command="onBatchCommand">
          <el-button type="primary" :disabled="!selectedRows.length">
            批量操作
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="publish">批量发布</el-dropdown-item>
              <el-dropdown-item command="unpublish">批量反发布</el-dropdown-item>
              <el-dropdown-item command="delete" divided>批量删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <div class="page-list-body">
        <div class="page-list-table">
          <el-table :data="rows" height="100%" @selection-change="onSelectionChange">
            <el-table-column type="selection" width="48" />
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="title" label="场次标题" min-width="120" show-overflow-tooltip />
            <el-table-column label="试卷名称" min-width="130" show-overflow-tooltip>
              <template #default="{ row }">{{ (row.paper_title as string) || "—" }}</template>
            </el-table-column>
            <el-table-column label="试卷编号" width="120" show-overflow-tooltip>
              <template #default="{ row }">{{ (row.paper_no as string) || "—" }}</template>
            </el-table-column>
            <el-table-column label="试卷类型" width="88">
              <template #default="{ row }">{{ paperTypeLabel(row.paper_type as string) }}</template>
            </el-table-column>
            <el-table-column label="次数限制" width="100" align="center">
              <template #default="{ row }">
                {{ attemptLimitDisplay(row) }}
              </template>
            </el-table-column>
            <el-table-column label="发布员" width="100" show-overflow-tooltip>
              <template #default="{ row }">{{ (row.publisher_name as string) || "—" }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">{{ sessionStatusCn(row.status as string) }}</template>
            </el-table-column>
            <el-table-column label="开始" width="170">
              <template #default="{ row }">{{ fmt(row.start_at) }}</template>
            </el-table-column>
            <el-table-column label="结束" width="170">
              <template #default="{ row }">{{ fmt(row.end_at) }}</template>
            </el-table-column>
            <el-table-column v-if="canManage" label="操作" width="340" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" :disabled="!isDraftSession(row)" @click="openEdit(row)">编辑</el-button>
                <el-tooltip
                  v-if="row.status !== 'published'"
                  :disabled="canPublishSession(row)"
                  content="仅在考试开放时间内可发布，请先设置开始与结束时间"
                  placement="top"
                >
                  <span class="op-inline">
                    <el-button link type="success" :disabled="!canPublishSession(row)" @click="publish(row)">发布</el-button>
                  </span>
                </el-tooltip>
                <el-button v-if="row.status === 'published'" link type="warning" @click="unpublish(row)">反发布</el-button>
                <el-button link type="primary" @click="printRow(row)">打印</el-button>
                <el-button link type="danger" :disabled="!isDraftSession(row)" @click="removeOne(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="page-list-pager">
          <el-pagination
            background
            layout="prev, pager, next"
            :total="total"
            :page-size="limit"
            @current-change="(p: number) => { page = p; load(); }"
          />
        </div>
      </div>
    </el-card>

    <el-dialog v-model="dlg" :title="form.id ? '编辑场次' : '新建场次'" width="580px">
      <el-form label-width="110px">
        <el-form-item label="场次编码">
          <el-input v-model="form.session_code" placeholder="留空则保存时自动生成" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="所属企业" required>
          <el-select
            v-model="form.enterprise_id"
            placeholder="选择企业"
            filterable
            style="width: 100%"
            @change="onEnterpriseChange"
          >
            <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程" required>
          <el-select
            v-model="form.course_id"
            placeholder="选择课程"
            filterable
            style="width: 100%"
            :disabled="!form.enterprise_id"
            @change="onCourseChange"
          >
            <el-option v-for="c in courseOpts" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="试卷" required>
          <el-select
            v-model="form.paper_id"
            placeholder="选择试卷"
            filterable
            style="width: 100%"
            :disabled="!form.course_id"
            @change="onPaperChange"
          >
            <el-option v-for="p in paperOpts" :key="p.id" :label="paperOptLabel(p)" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="次数限制">
          <span v-if="selectedPaperType === 'practice'" class="muted">练习卷不限制次数</span>
          <el-input-number v-else v-model="form.attempt_limit" :min="1" :max="9999" />
        </el-form-item>
        <el-form-item label="标题" required><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="form.start_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss.SSSZ" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="form.end_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss.SSSZ" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ArrowDown } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import {
  listSessions,
  createSession,
  updateSession,
  publishSession,
  unpublishSession,
  deleteSession,
} from "@/api/sessions";
import { listEnterprises } from "@/api/enterprises";
import { listCourses } from "@/api/courses";
import { listPapers, getPaper } from "@/api/papers";
import { resolvePrintTemplate } from "@/api/print_templates";
import { buildPaperPrintHtml, openPaperPrint } from "@/plugins/paperPrint";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const canManage = computed(() => auth.canAny("action.session.manage", "menu.exam.paper_publish"));

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const dlg = ref(false);
const filterTitleKw = ref("");
const selectedRows = ref<Record<string, unknown>[]>([]);

const enterpriseOpts = ref<{ id: number; name: string }[]>([]);
const courseOpts = ref<{ id: number; name: string }[]>([]);
const paperOpts = ref<
  { id: number; title: string; paper_no?: string | null; course_id?: number | null; paper_type?: string }[]
>([]);

const form = reactive({
  id: 0,
  session_code: "",
  enterprise_id: null as number | null,
  course_id: null as number | null,
  paper_id: null as number | null,
  attempt_limit: 1,
  title: "",
  start_at: "" as string | undefined,
  end_at: "" as string | undefined,
});

const selectedPaperType = computed(() => {
  const p = paperOpts.value.find((x) => x.id === form.paper_id);
  return p?.paper_type || "";
});

function fmt(v: unknown) {
  if (!v) return "";
  return String(v).replace("T", " ").slice(0, 19);
}

function sessionStatusCn(status: string) {
  if (status === "published") return "已发布";
  if (status === "closed") return "已结束";
  return "草稿";
}

function paperTypeLabel(t: string | undefined) {
  if (t === "practice") return "练习";
  if (t === "mock") return "模拟";
  if (t === "formal") return "正式";
  return t || "—";
}

function attemptLimitDisplay(row: Record<string, unknown>) {
  if (row.paper_type === "practice") return "无限制";
  const n = row.attempt_limit;
  if (n == null || n === "") return "—";
  return String(n);
}

function isDraftSession(row: Record<string, unknown>) {
  return row.status === "draft";
}

function canPublishSession(row: Record<string, unknown>) {
  if (row.status !== "draft") return false;
  const start = row.start_at;
  const end = row.end_at;
  if (!start || !end) return false;
  const t = Date.now();
  const s = new Date(String(start)).getTime();
  const e = new Date(String(end)).getTime();
  if (Number.isNaN(s) || Number.isNaN(e)) return false;
  return t >= s && t <= e;
}

function paperOptLabel(p: { id: number; title: string; paper_no?: string | null }) {
  const no = p.paper_no != null && String(p.paper_no).trim() !== "" ? String(p.paper_no) : `#${p.id}`;
  return `${p.title}（${no}）`;
}

async function loadEnterpriseOptions() {
  const { data } = await listEnterprises({ skip: 0, limit: 500 });
  enterpriseOpts.value = (data.items || []).map((x: { id: number; name: string }) => ({ id: x.id, name: x.name }));
}

async function loadCoursesForEnterprise(eid: number | null) {
  courseOpts.value = [];
  if (!eid) return;
  const { data } = await listCourses({ skip: 0, limit: 500, enterprise_id: eid });
  courseOpts.value = (data.items || []).map((x: { id: number; name: string }) => ({ id: x.id, name: x.name }));
}

async function loadPapersForCourse(cid: number | null) {
  paperOpts.value = [];
  if (!cid) return;
  const { data } = await listPapers({ skip: 0, limit: 200, course_id: cid });
  paperOpts.value = (data.items || []).map(
    (x: { id: number; title: string; paper_no?: string | null; course_id?: number | null; paper_type?: string }) => ({
      id: x.id,
      title: x.title,
      paper_no: x.paper_no,
      course_id: x.course_id,
      paper_type: x.paper_type,
    })
  );
}

async function onEnterpriseChange() {
  form.course_id = null;
  form.paper_id = null;
  await loadCoursesForEnterprise(form.enterprise_id);
}

async function onCourseChange() {
  form.paper_id = null;
  await loadPapersForCourse(form.course_id);
}

function onPaperChange() {
  const p = paperOpts.value.find((x) => x.id === form.paper_id);
  if (p?.paper_type === "practice") form.attempt_limit = 1;
}

function onSelectionChange(sel: Record<string, unknown>[]) {
  selectedRows.value = sel;
}

function doSearch() {
  page.value = 1;
  void load();
}

async function load() {
  try {
    const skip = (page.value - 1) * limit.value;
    const params: Record<string, unknown> = { skip, limit: limit.value };
    const tk = filterTitleKw.value.trim();
    if (tk) params.title_keyword = tk;
    const { data } = await listSessions(params);
    total.value = data.total;
    rows.value = data.items;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载失败"));
  }
}

async function openCreate() {
  form.id = 0;
  form.session_code = "";
  form.title = "";
  form.start_at = undefined;
  form.end_at = undefined;
  form.attempt_limit = 1;
  const defEnt = auth.me?.enterprise_id ?? enterpriseOpts.value[0]?.id ?? null;
  form.enterprise_id = defEnt;
  form.course_id = null;
  form.paper_id = null;
  if (defEnt) await loadCoursesForEnterprise(defEnt);
  else courseOpts.value = [];
  paperOpts.value = [];
  dlg.value = true;
}

async function openEdit(row: Record<string, unknown>) {
  if (row.status !== "draft") {
    ElMessage.warning("仅草稿场次可编辑");
    return;
  }
  form.id = row.id as number;
  form.session_code = (row.session_code as string) || "";
  form.title = (row.title as string) || "";
  form.start_at = row.start_at as string | undefined;
  form.end_at = row.end_at as string | undefined;
  form.enterprise_id = (row.enterprise_id as number) || null;
  form.course_id = (row.course_id as number) || null;
  form.paper_id = (row.paper_id as number) || null;
  const lim = row.attempt_limit;
  form.attempt_limit = row.paper_type === "practice" ? 1 : lim != null ? Number(lim) : 1;
  if (form.enterprise_id) await loadCoursesForEnterprise(form.enterprise_id);
  if (form.course_id) await loadPapersForCourse(form.course_id);
  dlg.value = true;
}

async function save() {
  if (!form.title.trim() || !form.enterprise_id || !form.course_id || !form.paper_id) {
    ElMessage.warning("请填写企业、课程、试卷与标题");
    return;
  }
  const code = (form.session_code || "").trim();
  const body: Record<string, unknown> = {
    enterprise_id: form.enterprise_id,
    course_id: form.course_id,
    paper_id: form.paper_id,
    title: form.title.trim(),
    start_at: form.start_at || null,
    end_at: form.end_at || null,
  };
  if (selectedPaperType.value !== "practice") {
    body.attempt_limit = form.attempt_limit;
  }
  if (form.id) {
    body.session_code = code;
  } else if (code) {
    body.session_code = code;
  }
  try {
    if (!form.id) await createSession(body);
    else
      await updateSession(form.id, {
        session_code: code,
        enterprise_id: form.enterprise_id,
        course_id: form.course_id,
        paper_id: form.paper_id,
        title: form.title.trim(),
        start_at: form.start_at || null,
        end_at: form.end_at || null,
        attempt_limit: selectedPaperType.value === "practice" ? null : form.attempt_limit,
      });
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

async function publish(row: Record<string, unknown>) {
  if (!canPublishSession(row)) {
    ElMessage.warning("仅在考试开放时间内可发布，请先设置开始与结束时间");
    return;
  }
  try {
    await publishSession(row.id as number);
    ElMessage.success("已发布");
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "发布失败"));
  }
}

async function unpublish(row: Record<string, unknown>) {
  try {
    await unpublishSession(row.id as number);
    ElMessage.success("已反发布");
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "反发布失败"));
  }
}

async function removeOne(row: Record<string, unknown>) {
  if (row.status !== "draft") {
    ElMessage.warning("仅草稿场次可删除");
    return;
  }
  try {
    await ElMessageBox.confirm(`确定删除场次「${row.title}」？`, "删除确认", { type: "warning" });
  } catch {
    return;
  }
  try {
    await deleteSession(row.id as number);
    ElMessage.success("已删除");
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "删除失败"));
  }
}

async function printRow(row: Record<string, unknown>) {
  const cid = row.course_id as number | undefined;
  if (!cid) {
    ElMessage.warning("场次无关联课程，无法匹配打印模板");
    return;
  }
  try {
    const res = await resolvePrintTemplate(cid);
    const tmpl = res.data;
    if (!tmpl || !tmpl.layout_json) {
      ElMessage.warning("该课程无已发布的打印模板，请先在打印设置中按课程发布模板");
      return;
    }
    const { data: paper } = await getPaper(row.paper_id as number);
    const items = (paper.items || []) as Array<{ question?: { stem?: string } }>;
    const blocks = items.map((it, i) => {
      const stem = it.question?.stem || "";
      const safe = stem.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br/>");
      return `<div><strong>${i + 1}.</strong> ${safe}</div>`;
    });
    const html = buildPaperPrintHtml(tmpl.layout_json as Record<string, unknown>, {
      paperTitle: String((row.paper_title as string) || paper.title || "试卷"),
      questionBlocks: blocks.length ? blocks : ["（暂无题目明细，请在试卷管理中组卷）"],
    });
    openPaperPrint(html);
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "打印失败"));
  }
}

async function onBatchCommand(cmd: string) {
  const sel = selectedRows.value;
  if (!sel.length) return;
  if (cmd === "publish") {
    const targets = sel.filter((r) => canPublishSession(r));
    if (!targets.length) {
      ElMessage.info("所选行中没有可在当前时段发布的草稿场次");
      return;
    }
    try {
      for (const r of targets) {
        await publishSession(r.id as number);
      }
      ElMessage.success(`已发布 ${targets.length} 条`);
      await load();
    } catch (e) {
      ElMessage.error(apiErrorMessage(e, "批量发布失败"));
    }
    return;
  }
  if (cmd === "unpublish") {
    const targets = sel.filter((r) => r.status === "published");
    if (!targets.length) {
      ElMessage.info("所选行没有已发布场次");
      return;
    }
    try {
      for (const r of targets) {
        await unpublishSession(r.id as number);
      }
      ElMessage.success(`已反发布 ${targets.length} 条`);
      await load();
    } catch (e) {
      ElMessage.error(apiErrorMessage(e, "批量反发布失败"));
    }
    return;
  }
  if (cmd === "delete") {
    const targets = sel.filter((r) => r.status === "draft");
    if (!targets.length) {
      ElMessage.info("所选中没有可删除的草稿场次");
      return;
    }
    try {
      await ElMessageBox.confirm(`确定删除选中的 ${targets.length} 条草稿场次？`, "批量删除", { type: "warning" });
    } catch {
      return;
    }
    try {
      for (const r of targets) {
        await deleteSession(r.id as number);
      }
      ElMessage.success("已删除");
      await load();
    } catch (e) {
      ElMessage.error(apiErrorMessage(e, "批量删除失败"));
    }
  }
}

onMounted(async () => {
  await loadEnterpriseOptions();
  await load();
});
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.op-inline {
  display: inline-flex;
  vertical-align: middle;
}
.muted {
  color: #909399;
  font-size: 13px;
}
</style>
