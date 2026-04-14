<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title"><AppEmoji name="paperManage" size="sm" decorative />试卷管理</div>
      </template>
      <div class="page-list-toolbar toolbar">
      <el-input
        v-model="filterTitle"
        clearable
        placeholder="试卷名称"
        style="width: 150px"
        @keyup.enter="doSearch"
      />
      <el-input
        v-model="filterCourse"
        clearable
        placeholder="课程"
        style="width: 130px"
        @keyup.enter="doSearch"
      />
      <el-input
        v-model="filterEnterprise"
        clearable
        placeholder="所属企业"
        style="width: 150px"
        @keyup.enter="doSearch"
      />
      <el-select v-model="filterPaperType" clearable placeholder="试卷类型" style="width: 120px" @change="doSearch">
        <el-option label="正式" value="formal" />
        <el-option label="模拟" value="mock" />
        <el-option label="练习" value="practice" />
      </el-select>
      <el-button type="primary" @click="doSearch">查询</el-button>
      <el-button type="success" @click="openCreate"><AppEmoji name="add" size="sm" decorative />新建试卷</el-button>
      <el-button :disabled="!selectedRows.length" @click="batchCompose">批量组卷</el-button>
      <el-button type="warning" plain :disabled="!selectedRows.length" @click="batchUncompose">批量反组卷</el-button>
      <el-button type="danger" plain :disabled="!selectedRows.length" @click="batchDelete">批量删除</el-button>
    </div>
    <div class="page-list-body">
      <div class="page-list-table">
        <el-table :data="rows" height="100%" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="48" />
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="paper_no" label="试卷编号" width="150" show-overflow-tooltip />
      <el-table-column prop="title" label="试卷名称" min-width="140" show-overflow-tooltip />
      <el-table-column label="所属企业" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ (row.enterprise_name as string) || "—" }}</template>
      </el-table-column>
      <el-table-column label="课程" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ (row.course_name as string) || "—" }}</template>
      </el-table-column>
      <el-table-column label="试卷类型" width="100">
        <template #default="{ row }">{{ paperTypeLabel(row.paper_type as string) }}</template>
      </el-table-column>
      <el-table-column label="等级" width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ (row.level_name as string) || "—" }}</template>
      </el-table-column>
      <el-table-column prop="duration_minutes" label="时长(分)" width="100" />
      <el-table-column label="总分" width="90">
        <template #default="{ row }">{{ formatScore(row.total_score) }}</template>
      </el-table-column>
      <el-table-column label="题量" width="72" align="center">
        <template #default="{ row }">{{ paperItemCount(row) }}</template>
      </el-table-column>
      <el-table-column label="场次引用" width="88" align="center">
        <template #default="{ row }">{{ paperSessionRefs(row) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="280">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push('/papers/' + row.id)"
            ><AppEmoji name="compose" size="sm" decorative />组卷</el-button
          >
          <el-button
            link
            type="warning"
            :disabled="!canUncomposeRow(row)"
            @click="onUncompose(row)"
            >反组卷</el-button
          >
          <el-button link type="danger" :disabled="!canDeleteRow(row)" @click="onDel(row)"
            ><AppEmoji name="delete" size="sm" decorative />删除</el-button
          >
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

    <el-dialog v-model="dlg" title="新建试卷" width="860px" top="5vh" @closed="onDlgClosed">
      <el-form label-width="120px">
        <el-form-item v-if="auth.isAdmin" label="所属企业" required>
          <el-select
            v-model="form.enterprise_id"
            placeholder="请选择企业（与企业信息一致，再选课程）"
            filterable
            style="width: 100%"
            @change="onEnterpriseChange"
          >
            <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-else label="所属企业">
          <el-input :model-value="auth.me?.enterprise?.name || '—'" disabled />
        </el-form-item>

        <el-form-item label="组卷方式">
          <el-radio-group v-model="createMode">
            <el-radio-button value="single">单套组卷</el-radio-button>
            <el-radio-button value="batch">多套批量</el-radio-button>
          </el-radio-group>
          <span class="hint">多套：按各题型「总量」自动均分到各套，题目互不重复</span>
        </el-form-item>

        <el-form-item label="关联课程" required>
          <el-select
            v-model="form.course_id"
            placeholder="选择课程（请先选企业，可输入名称搜索）"
            filterable
            remote
            reserve-keyword
            style="width: 100%"
            :disabled="auth.isAdmin && !form.enterprise_id"
            :remote-method="remoteCourses"
            :loading="courseLoading"
            @visible-change="onCourseSelectVisible"
          >
            <el-option v-for="c in courseOpts" :key="c.id" :label="courseOptLabel(c)" :value="c.id" />
          </el-select>
        </el-form-item>

        <template v-if="createMode === 'single'">
          <el-form-item label="试卷名称" required>
            <el-input v-model="form.title" placeholder="试卷名称" />
          </el-form-item>
          <el-form-item label="试卷编号">
            <el-input v-model="form.paper_no" clearable placeholder="留空则自动生成" />
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="试卷名称前缀" required>
            <el-input v-model="batchForm.base_title" placeholder="多套时自动加「第N套」" />
          </el-form-item>
          <el-form-item label="生成套数" required>
            <el-input-number v-model="batchForm.paper_count" :min="1" :max="50" />
          </el-form-item>
        </template>

        <el-form-item label="试卷类型">
          <el-select v-model="form.paper_type" style="width: 100%">
            <el-option label="正式" value="formal" />
            <el-option label="模拟" value="mock" />
            <el-option label="练习" value="practice" />
          </el-select>
        </el-form-item>
        <el-form-item label="试卷等级">
          <el-select v-model="form.level_id" clearable placeholder="可选" filterable style="width: 100%">
            <el-option v-for="lv in levelOpts" :key="lv.id" :label="`${lv.level_name}（${lv.level_code}）`" :value="lv.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="时长(分)">
          <el-input-number v-model="form.duration_minutes" :min="1" :max="600" />
        </el-form-item>

        <template v-if="createMode === 'single'">
          <el-divider content-position="left">按题型抽题（题库区间为所选课程下已发布题目）</el-divider>
          <div class="rules-toolbar">
            <el-button type="primary" link @click="addRuleRow">增加题型行</el-button>
          </div>
          <el-table :data="ruleRows" border size="small" class="rules-table">
            <el-table-column label="题型" width="120">
              <template #default="{ row }">
                <el-select v-model="row.q_type" placeholder="题型" style="width: 100%">
                  <el-option v-for="o in qTypeOpts" :key="o.value" :label="o.label" :value="o.value" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="全选" width="72" align="center">
              <template #default="{ row }">
                <el-checkbox v-model="row.use_all" />
              </template>
            </el-table-column>
            <el-table-column label="数量" width="100">
              <template #default="{ row }">
                <el-input-number v-model="row.count" :min="0" :disabled="row.use_all" controls-position="right" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="自动拆分" width="110">
              <template #default="{ row }">
                <el-input-number v-model="row.auto_split" :min="1" controls-position="right" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="单题分值" width="110">
              <template #default="{ row }">
                <el-input-number v-model="row.score_per" :min="0" :step="0.5" controls-position="right" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ $index }">
                <el-button type="danger" link :disabled="ruleRows.length <= 1" @click="removeRuleRow($index)">删</el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>

        <template v-else>
          <el-divider content-position="left">题型总量（将自动均分到各套；各套之间题目不重复）</el-divider>
          <el-table :data="batchRuleRows" border size="small" class="rules-table">
            <el-table-column label="题型" width="120">
              <template #default="{ row }">
                <span>{{ qTypeLabel(row.q_type) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="题型总量" min-width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.total_count" :min="0" controls-position="right" style="width: 100%" />
              </template>
            </el-table-column>
          </el-table>
          <el-form-item label="自动拆分" class="mt12">
            <el-input-number v-model="batchForm.auto_split" :min="1" />
          </el-form-item>
          <el-form-item label="单题分值">
            <el-input-number v-model="batchForm.score_per" :min="0" :step="0.5" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="createMode === 'single' ? saveCreate() : saveBatch()">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { listPapers, createPaper, createPapersBatch, deletePaper, clearPaperItems } from "@/api/papers";
import { listCourses } from "@/api/courses";
import { listPaperLevels } from "@/api/paper_levels";
import { listEnterprises } from "@/api/enterprises";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

const paperTypeLabelMap: Record<string, string> = {
  formal: "正式",
  mock: "模拟",
  practice: "练习",
};

function paperTypeLabel(code: string | undefined) {
  if (!code) return "—";
  return paperTypeLabelMap[code] ?? code;
}

function formatScore(v: unknown) {
  if (v == null || v === "") return "0";
  const n = Number(v);
  return Number.isFinite(n) ? String(n) : String(v);
}

function paperItemCount(row: Record<string, unknown>) {
  const n = Number(row.item_count);
  return Number.isFinite(n) ? n : 0;
}

function paperSessionRefs(row: Record<string, unknown>) {
  const n = Number(row.session_ref_count);
  return Number.isFinite(n) ? n : 0;
}

function canDeleteRow(row: Record<string, unknown>) {
  return paperItemCount(row) < 1 && paperSessionRefs(row) < 1;
}

function canUncomposeRow(row: Record<string, unknown>) {
  return paperItemCount(row) > 0 && paperSessionRefs(row) < 1;
}

function onSelectionChange(sel: Record<string, unknown>[]) {
  selectedRows.value = sel;
}
const rows = ref<Record<string, unknown>[]>([]);
const selectedRows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const filterTitle = ref("");
const filterCourse = ref("");
const filterEnterprise = ref("");
const filterPaperType = ref<string | undefined>();
const dlg = ref(false);
const createMode = ref<"single" | "batch">("single");

const enterpriseOpts = ref<{ id: number; name: string }[]>([]);
const form = reactive({
  enterprise_id: undefined as number | undefined,
  title: "",
  paper_no: "",
  course_id: undefined as number | undefined,
  paper_type: "formal",
  level_id: undefined as number | undefined,
  description: "",
  duration_minutes: 60,
});

const batchForm = reactive({
  base_title: "",
  paper_count: 3,
  auto_split: 1,
  score_per: 1,
});

type CourseOpt = { id: number; name: string; enterprise?: { id: number; name: string } };
const courseOpts = ref<CourseOpt[]>([]);
const courseLoading = ref(false);
const levelOpts = ref<{ id: number; level_name: string; level_code: string }[]>([]);

const qTypeOpts = [
  { value: "judge", label: "判断" },
  { value: "single", label: "单选" },
  { value: "multiple", label: "多选" },
  { value: "fill", label: "填空" },
];

function qTypeLabel(q: string) {
  return qTypeOpts.find((o) => o.value === q)?.label || q;
}

interface RuleRow {
  q_type: string;
  use_all: boolean;
  count: number;
  auto_split: number;
  score_per: number;
}

interface BatchRuleRow {
  q_type: string;
  total_count: number;
}

function defaultRuleRow(): RuleRow {
  return { q_type: "single", use_all: false, count: 5, auto_split: 1, score_per: 1 };
}

function defaultBatchRuleRows(): BatchRuleRow[] {
  return qTypeOpts.map((o) => ({ q_type: o.value, total_count: 0 }));
}

const ruleRows = ref<RuleRow[]>([defaultRuleRow()]);
const batchRuleRows = ref<BatchRuleRow[]>(defaultBatchRuleRows());

function courseOptLabel(c: CourseOpt) {
  const en = c.enterprise?.name;
  return en ? `${c.name}（${en}）` : c.name;
}

function resolveCourseEnterpriseId(): number | undefined {
  if (auth.isAdmin) return form.enterprise_id;
  return auth.me?.enterprise_id ?? undefined;
}

async function load() {
  const skip = (page.value - 1) * limit.value;
  const params: Record<string, unknown> = { skip, limit: limit.value };
  const t = filterTitle.value.trim();
  const c = filterCourse.value.trim();
  const e = filterEnterprise.value.trim();
  if (t) params.title_keyword = t;
  if (c) params.course_keyword = c;
  if (e) params.enterprise_keyword = e;
  if (filterPaperType.value) params.paper_type_keyword = filterPaperType.value;
  const { data } = await listPapers(params);
  total.value = data.total;
  rows.value = data.items;
}

function doSearch() {
  page.value = 1;
  void load();
}

/** 关键字变更后短暂防抖自动查询（挂载完成后生效，避免与首次 load 重复） */
const suppressFilterWatch = ref(true);
let filterDebounce: ReturnType<typeof setTimeout> | null = null;
watch([filterTitle, filterCourse, filterEnterprise], () => {
  if (suppressFilterWatch.value) return;
  if (filterDebounce) clearTimeout(filterDebounce);
  filterDebounce = setTimeout(() => {
    filterDebounce = null;
    doSearch();
  }, 400);
});

/** 分页上限与后端 PageParams.limit 一致（≤200），避免 422 导致下拉无数据 */
async function reloadCoursesForEnterprise(eid: number | undefined, keyword = "") {
  const params: Record<string, unknown> = { skip: 0, limit: 200 };
  const kw = keyword.trim();
  if (kw) params.keyword = kw;
  if (auth.isAdmin && eid) {
    params.enterprise_id = eid;
  }
  courseLoading.value = true;
  try {
    const { data } = await listCourses(params);
    courseOpts.value = (data.items || []) as CourseOpt[];
    if (form.course_id != null && !courseOpts.value.some((c) => c.id === form.course_id)) {
      form.course_id = undefined;
    }
  } catch {
    courseOpts.value = [];
    form.course_id = undefined;
  } finally {
    courseLoading.value = false;
  }
}

async function remoteCourses(query: string) {
  await reloadCoursesForEnterprise(resolveCourseEnterpriseId(), query);
}

function onCourseSelectVisible(visible: boolean) {
  if (visible) void reloadCoursesForEnterprise(resolveCourseEnterpriseId(), "");
}

/** 超管按所选企业筛选等级档案；企业用户由后端按登录企业过滤 */
async function loadPaperLevelsForForm(enterpriseId: number | undefined) {
  const params: Record<string, unknown> = { skip: 0, limit: 200 };
  if (auth.isAdmin && enterpriseId) {
    params.enterprise_id = enterpriseId;
  }
  try {
    const { data } = await listPaperLevels(params);
    levelOpts.value = (data.items || []) as { id: number; level_name: string; level_code: string }[];
    if (form.level_id != null && !levelOpts.value.some((lv) => lv.id === form.level_id)) {
      form.level_id = undefined;
    }
  } catch {
    levelOpts.value = [];
  }
}

function onEnterpriseChange() {
  form.course_id = undefined;
  form.level_id = undefined;
  void reloadCoursesForEnterprise(form.enterprise_id, "");
  void loadPaperLevelsForForm(form.enterprise_id);
}

function onDlgClosed() {
  createMode.value = "single";
}

function openCreate() {
  createMode.value = "single";
  form.title = "";
  form.paper_no = "";
  form.paper_type = "formal";
  form.level_id = undefined;
  form.description = "";
  form.duration_minutes = 60;
  batchForm.base_title = "";
  batchForm.paper_count = 3;
  batchForm.auto_split = 1;
  batchForm.score_per = 1;
  ruleRows.value = [defaultRuleRow()];
  batchRuleRows.value = defaultBatchRuleRows();
  if (auth.isAdmin) {
    form.enterprise_id = enterpriseOpts.value[0]?.id;
  } else {
    form.enterprise_id = auth.me?.enterprise_id ?? undefined;
  }
  dlg.value = true;
  void reloadCoursesForEnterprise(resolveCourseEnterpriseId(), "");
  void loadPaperLevelsForForm(auth.isAdmin ? form.enterprise_id : undefined);
}

function addRuleRow() {
  ruleRows.value.push(defaultRuleRow());
}

function removeRuleRow(i: number) {
  if (ruleRows.value.length <= 1) return;
  ruleRows.value.splice(i, 1);
}

async function saveCreate() {
  if (!form.title.trim()) {
    ElMessage.warning("请填写试卷名称");
    return;
  }
  if (!form.course_id) {
    ElMessage.warning("请选择关联课程");
    return;
  }
  if (auth.isAdmin && !form.enterprise_id) {
    ElMessage.warning("请选择所属企业");
    return;
  }
  const rulesPayload = ruleRows.value
    .filter((r) => r.q_type)
    .map((r) => ({
      q_type: r.q_type,
      use_all: r.use_all,
      count: r.use_all ? 0 : r.count,
      auto_split: r.auto_split,
      score_per: r.score_per,
    }));
  if (rulesPayload.length) {
    for (const r of rulesPayload) {
      if (!r.use_all && r.count < 1) {
        ElMessage.warning("未勾选全选时，每种题型数量至少为 1");
        return;
      }
    }
  }
  const body: Record<string, unknown> = {
    title: form.title.trim(),
    course_id: form.course_id,
    paper_type: form.paper_type,
    duration_minutes: form.duration_minutes,
    description: form.description.trim() || null,
    rules: rulesPayload,
  };
  const pn = form.paper_no.trim();
  if (pn) body.paper_no = pn;
  if (form.level_id) body.level_id = form.level_id;
  try {
    const { data } = await createPaper(body);
    ElMessage.success("已创建");
    dlg.value = false;
    await router.push("/papers/" + data.id);
  } catch {
    ElMessage.error("创建失败（请检查课程题库是否已有对应题型已发布题目）");
  }
}

async function saveBatch() {
  if (!batchForm.base_title.trim()) {
    ElMessage.warning("请填写试卷名称前缀");
    return;
  }
  if (!form.course_id) {
    ElMessage.warning("请选择关联课程");
    return;
  }
  if (auth.isAdmin && !form.enterprise_id) {
    ElMessage.warning("请选择所属企业");
    return;
  }
  const rules = batchRuleRows.value
    .filter((r) => r.total_count > 0)
    .map((r) => ({ q_type: r.q_type, total_count: r.total_count }));
  if (!rules.length) {
    ElMessage.warning("请至少为一种题型填写大于0 的总量");
    return;
  }
  try {
    const { data } = await createPapersBatch({
      base_title: batchForm.base_title.trim(),
      paper_count: batchForm.paper_count,
      course_id: form.course_id,
      paper_type: form.paper_type,
      level_id: form.level_id || null,
      description: form.description.trim() || null,
      duration_minutes: form.duration_minutes,
      rules,
      auto_split: batchForm.auto_split,
      score_per: batchForm.score_per,
    });
    const n = (data.items as unknown[])?.length ?? 0;
    ElMessage.success(`已生成 ${n} 套试卷`);
    dlg.value = false;
    await load();
  } catch {
    ElMessage.error("批量创建失败（请检查各题型总量与题库是否足够，且套数不宜过大导致某套分不到题）");
  }
}

function batchCompose() {
  if (!selectedRows.value.length) {
    ElMessage.warning("请先勾选试卷");
    return;
  }
  if (selectedRows.value.length > 1) {
    ElMessage.warning("组卷请每次选择一套试卷");
    return;
  }
  router.push("/papers/" + selectedRows.value[0].id);
}

async function batchUncompose() {
  if (!selectedRows.value.length) {
    ElMessage.warning("请先勾选试卷");
    return;
  }
  const targets = selectedRows.value.filter((r) => canUncomposeRow(r));
  if (!targets.length) {
    ElMessage.warning("所选试卷无已组卷题目，或已被考试场次引用，无法反组卷");
    return;
  }
  await ElMessageBox.confirm(
    `确定对 ${targets.length} 套试卷清空题目（反组卷）？`,
    "批量反组卷",
    { type: "warning" },
  );
  let ok = 0;
  for (const r of targets) {
    try {
      await clearPaperItems(r.id as number);
      ok++;
    } catch (e) {
      ElMessage.error(apiErrorMessage(e, `「${r.title}」反组卷失败`));
    }
  }
  if (ok) ElMessage.success(`已反组卷 ${ok} 套`);
  await load();
}

async function batchDelete() {
  if (!selectedRows.value.length) {
    ElMessage.warning("请先勾选试卷");
    return;
  }
  const targets = selectedRows.value.filter((r) => canDeleteRow(r));
  if (!targets.length) {
    ElMessage.warning("仅可删除未组卷且未被考试场次引用的试卷");
    return;
  }
  await ElMessageBox.confirm(`确定删除选中的 ${targets.length} 套空试卷？`, "批量删除", { type: "warning" });
  let ok = 0;
  for (const r of targets) {
    try {
      await deletePaper(r.id as number);
      ok++;
    } catch (e) {
      ElMessage.error(apiErrorMessage(e, `「${r.title}」删除失败`));
    }
  }
  if (ok) ElMessage.success(`已删除 ${ok} 套`);
  await load();
}

async function onUncompose(row: Record<string, unknown>) {
  if (!canUncomposeRow(row)) return;
  await ElMessageBox.confirm(`确定清空「${row.title}」的全部题目？`, "反组卷", { type: "warning" });
  try {
    await clearPaperItems(row.id as number);
    ElMessage.success("已反组卷");
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "反组卷失败"));
  }
}

async function onDel(row: Record<string, unknown>) {
  if (!canDeleteRow(row)) {
    ElMessage.warning("已组卷或已被场次引用的试卷不可删除");
    return;
  }
  await ElMessageBox.confirm("确定删除该试卷？", "提示", { type: "warning" });
  try {
    await deletePaper(row.id as number);
    ElMessage.success("已删除");
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "删除失败"));
  }
}

onMounted(async () => {
  if (auth.isAdmin) {
    try {
      const { data } = await listEnterprises({ skip: 0, limit: 200 });
      enterpriseOpts.value = (data.items || []) as { id: number; name: string }[];
    } catch {
      enterpriseOpts.value = [];
    }
  }
  await load();
  suppressFilterWatch.value = false;
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
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.rules-toolbar {
  margin-bottom: 8px;
}
.rules-table {
  margin-bottom: 8px;
}
.hint {
  margin-left: 12px;
  color: #94a3b8;
  font-size: 12px;
}
.mt12 {
  margin-top: 12px;
}
</style>
