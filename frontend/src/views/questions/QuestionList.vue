<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title">
          <AppEmoji name="questionManage" size="sm" decorative />题库管理
        </div>
      </template>
      <div class="page-list-toolbar toolbar">
      <el-select v-model="filterType" clearable placeholder="题型" style="width: 140px">
        <el-option label="判断" value="judge" />
        <el-option label="单选" value="single" />
        <el-option label="多选" value="multiple" />
        <el-option label="填空" value="fill" />
      </el-select>
      <el-select v-model="filterStatus" clearable placeholder="状态" style="width: 140px">
        <el-option label="草稿" value="draft" />
        <el-option label="已发布" value="published" />
        <el-option label="禁用" value="disabled" />
      </el-select>
      <el-select
        v-model="filterCourseId"
        clearable
        filterable
        remote
        reserve-keyword
        placeholder="课程（输入名称模糊搜）"
        :remote-method="remoteToolbarCourses"
        :loading="toolbarCourseLoading"
        style="width: 240px"
        @visible-change="(v: boolean) => v && remoteToolbarCourses('')"
      >
        <el-option v-for="c in toolbarCourseOpts" :key="c.id" :label="c.label" :value="c.id" />
      </el-select>
      <el-input
        v-model="filterStem"
        clearable
        placeholder="题干关键字"
        style="width: 180px"
        @keyup.enter="doSearch"
      />
      <el-button type="primary" @click="doSearch"><AppEmoji name="search" size="sm" decorative />查询</el-button>
      <el-button type="success" @click="openEdit()"><AppEmoji name="add" size="sm" decorative />新建题目</el-button>
      <el-button v-if="auth.can('action.question.import')" type="warning" @click="openImport">导入题库</el-button>
      <el-button v-if="lastImportLogText" @click="downloadImportLog">下载导入日志</el-button>
      <el-dropdown
        v-if="auth.can('action.question.batch') || auth.can('action.question.manage')"
        trigger="click"
        @command="onBatchCommand"
      >
        <el-button type="primary" :disabled="!selectedRows.length">
          批量操作<el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-if="auth.can('action.question.batch')" command="publish">发布</el-dropdown-item>
            <el-dropdown-item v-if="auth.can('action.question.batch')" command="unpublish">反发布</el-dropdown-item>
            <el-dropdown-item v-if="auth.can('action.question.batch')" command="disable">禁用</el-dropdown-item>
            <el-dropdown-item v-if="auth.can('action.question.batch')" command="enable">反禁用</el-dropdown-item>
            <el-dropdown-item
              v-if="auth.can('action.question.manage')"
              command="difficulty"
              :divided="auth.can('action.question.batch')"
            >
              难度系数
            </el-dropdown-item>
            <el-dropdown-item
              v-if="auth.can('action.question.manage')"
              command="delete"
              :divided="auth.can('action.question.batch') || auth.can('action.question.manage')"
            >
              删除
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
    <div class="page-list-body">
      <div class="page-list-table">
        <el-table :data="rows" height="100%" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="48" />
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="question_no" label="题号" width="130" show-overflow-tooltip />
      <el-table-column label="题型" width="90">
        <template #default="{ row }">{{ qTypeLabel[row.q_type as string] ?? row.q_type }}</template>
      </el-table-column>
      <el-table-column prop="stem" label="题干" show-overflow-tooltip />
      <el-table-column label="课程" width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.course_name ?? "—" }}</template>
      </el-table-column>
      <el-table-column label="企业" width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.enterprise_name ?? "—" }}</template>
      </el-table-column>
      <el-table-column prop="difficulty" label="难度" width="72" align="center" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">{{ statusLabel[row.status as string] ?? row.status }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button link type="primary" @click="openView(row)">查看</el-button>
          <el-button link type="primary" @click="openEdit(row)"><AppEmoji name="edit" size="sm" decorative />编辑</el-button>
          <el-button
            link
            type="danger"
            :disabled="row.status !== 'draft'"
            :title="row.status !== 'draft' ? '仅草稿可删除；已发布请先反发布，已禁用请先反禁用' : ''"
            @click="onDel(row)"
            ><AppEmoji name="delete" size="sm" decorative />删除</el-button
          >
        </template>
      </el-table-column>
    </el-table>
      </div>
      <div class="page-list-pager">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :total="total"
          :page-size="limit"
          :page-sizes="[50, 100, 200]"
          @size-change="onPageSizeChange"
          @current-change="onPageChange"
        />
      </div>
    </div>
    </el-card>

    <el-dialog v-model="dlg" :title="form.id ? '编辑题目' : '新建题目'" width="640px">
      <el-form label-width="100px">
        <el-form-item label="所属企业">
          <el-select
            v-model="form.enterprise_id"
            clearable
            filterable
            remote
            reserve-keyword
            placeholder="输入企业名称搜索"
            :remote-method="remoteFormEnterprises"
            :loading="formEntLoading"
            style="width: 100%"
            @visible-change="(v: boolean) => v && remoteFormEnterprises('')"
            @change="onFormEnterpriseChange"
          >
            <el-option v-for="e in formEntOpts" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属课程">
          <el-select
            v-model="form.course_id"
            clearable
            filterable
            remote
            reserve-keyword
            placeholder="请先选企业，再输入课程名搜索"
            :disabled="!form.enterprise_id"
            :remote-method="remoteFormCourses"
            :loading="formCourseLoading"
            style="width: 100%"
            @visible-change="
              (v: boolean) => {
                if (v && form.enterprise_id) remoteFormCourses('');
              }
            "
          >
            <el-option v-for="c in formCourseOpts" :key="c.id" :label="courseOptLabel(c)" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.id" label="题号">
          <el-input :model-value="form.question_no || '—'" disabled />
        </el-form-item>
        <el-form-item v-else label="题号">
          <el-input model-value="保存后按企业、课程、题型自动生成" disabled />
        </el-form-item>
        <el-form-item label="题型">
          <el-select v-model="form.q_type" style="width: 100%">
            <el-option label="判断 judge" value="judge" />
            <el-option label="单选 single" value="single" />
            <el-option label="多选 multiple" value="multiple" />
            <el-option label="填空 fill" value="fill" />
          </el-select>
        </el-form-item>
        <el-form-item label="题干"
          ><el-input
            v-model="form.stem"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
            placeholder="仅题干与选项文字，不含答案与解析"
        /></el-form-item>
        <el-form-item label="选项（内容）">
          <el-input type="textarea" :model-value="optionsPreview" readonly :rows="4" class="readonly-preview" />
        </el-form-item>
        <el-form-item label="选项（JSON）"
          ><el-input v-model="optionsText" type="textarea" :rows="3" placeholder='如 [{"key":"A","text":"..."}]'
        /></el-form-item>
        <el-form-item label="标准答案（内容）">
          <el-input type="textarea" :model-value="answerPreview" readonly :rows="2" class="readonly-preview" />
        </el-form-item>
        <el-form-item label="标准答案（JSON）"
          ><el-input v-model="answerText" type="textarea" :rows="2" placeholder="见详设说明"
        /></el-form-item>
        <el-form-item label="解析（内容）"><el-input v-model="form.analysis" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="难度(1-5)"><el-input-number v-model="form.difficulty" :min="1" :max="5" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <template v-if="!form.id || form.status === 'draft'">
              <el-option label="草稿 draft" value="draft" />
              <el-option label="已发布 published" value="published" />
            </template>
            <template v-else-if="form.status === 'published'">
              <el-option label="草稿 draft" value="draft" />
              <el-option label="已发布 published" value="published" />
              <el-option label="禁用 disabled" value="disabled" />
            </template>
            <template v-else-if="form.status === 'disabled'">
              <el-option label="禁用 disabled" value="disabled" />
              <el-option label="已发布 published（反禁用）" value="published" />
            </template>
            <template v-else>
              <el-option label="草稿 draft" value="draft" />
              <el-option label="已发布 published" value="published" />
              <el-option label="禁用 disabled" value="disabled" />
            </template>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="viewDlg" title="查看题目" width="720px" destroy-on-close @closed="resetView">
      <div v-loading="viewLoading" class="view-body">
        <template v-if="viewDetail">
          <p class="view-meta">
            第 {{ viewNav?.index != null ? viewNav.index + 1 : "—" }} / {{ viewNav?.total ?? "—" }} 题（当前筛选范围内）
          </p>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="题号">{{ viewDetail.question_no }}</el-descriptions-item>
            <el-descriptions-item label="题型">{{ qTypeLabel[viewDetail.q_type] ?? viewDetail.q_type }}</el-descriptions-item>
            <el-descriptions-item label="课程">{{ viewDetail.course_name ?? "—" }}</el-descriptions-item>
            <el-descriptions-item label="企业">{{ viewDetail.enterprise_name ?? "—" }}</el-descriptions-item>
            <el-descriptions-item label="难度">{{ viewDetail.difficulty }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ statusLabel[viewDetail.status] ?? viewDetail.status }}</el-descriptions-item>
            <el-descriptions-item label="题干">
              <pre class="view-pre">{{ viewDetail.stem }}</pre>
            </el-descriptions-item>
            <el-descriptions-item v-if="viewDetail.options_json != null" label="选项">
              <pre class="view-pre">{{ formatOptionsForView(viewDetail.options_json) }}</pre>
            </el-descriptions-item>
            <el-descriptions-item label="答案">
              <pre class="view-pre">{{
                formatAnswerForView(viewDetail.answer_json, viewDetail.q_type, viewDetail.options_json)
              }}</pre>
            </el-descriptions-item>
            <el-descriptions-item v-if="viewDetail.analysis" label="解析">
              <pre class="view-pre">{{ viewDetail.analysis }}</pre>
            </el-descriptions-item>
          </el-descriptions>
        </template>
      </div>
      <template #footer>
        <el-button :disabled="!viewNav?.prev_id" @click="gotoViewNeighbor('prev')">上一题</el-button>
        <el-button :disabled="!viewNav?.next_id" @click="gotoViewNeighbor('next')">下一题</el-button>
        <el-button type="primary" @click="viewDlg = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDlg" title="导入题库" width="560px" @closed="resetImport">
      <el-form label-width="100px">
        <el-form-item label="所属企业" required>
          <el-select
            v-model="importEnterpriseId"
            filterable
            remote
            reserve-keyword
            placeholder="输入企业名称搜索"
            :remote-method="remoteImportEnterprises"
            :loading="importEntLoading"
            style="width: 100%"
            @visible-change="(v: boolean) => v && remoteImportEnterprises('')"
            @change="importCourseId = undefined"
          >
            <el-option v-for="e in importEntOpts" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属课程" required>
          <el-select
            v-model="importCourseId"
            filterable
            remote
            reserve-keyword
            placeholder="请先选企业，再输入课程名搜索"
            :disabled="!importEnterpriseId"
            :remote-method="remoteImportCourses"
            :loading="importCourseLoading"
            style="width: 100%"
            @visible-change="
              (v: boolean) => {
                if (v && importEnterpriseId) remoteImportCourses('');
              }
            "
          >
            <el-option v-for="c in importCourseOpts" :key="c.id" :label="courseOptLabel(c)" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="导入文件" required>
          <input
            ref="fileInputRef"
            type="file"
            multiple
            accept=".doc,.docx,.xls,.xlsx,.pdf,.txt,.csv,.png,.jpg,.jpeg,.gif,.webp,.bmp"
            @change="onImportFiles"
          />
          <p class="hint-text">
            支持多选：可同时上传「题干+选项」与「参考答案+试题解析」等文件；题干请带题号（如 169.），答案册使用「数字.【参考答案】」与「【试题解析】」，系统按题号自动合并。支持
            Word、Excel、PDF、图片、txt、CSV。
          </p>
          <p v-if="importFiles.length" class="hint-text">已选 {{ importFiles.length }} 个文件</p>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDlg = false">取消</el-button>
        <el-button type="primary" :loading="importLoading" @click="submitImport">开始导入</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="batchDifficultyDlg"
      title="批量设置难度系数"
      width="420px"
      destroy-on-close
      @closed="onBatchDifficultyClosed"
    >
      <p class="hint-text">已选 {{ batchDifficultyIds.length }} 道题目，将统一设为以下难度（1～5，数值越大表示难度越高）。</p>
      <el-form label-width="100px">
        <el-form-item label="难度系数">
          <el-input-number v-model="batchDifficultyValue" :min="1" :max="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDifficultyDlg = false">取消</el-button>
        <el-button type="primary" :loading="batchDifficultyLoading" @click="submitBatchDifficulty">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ArrowDown } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { listCourses } from "@/api/courses";
import { listEnterprises } from "@/api/enterprises";
import { apiErrorMessage } from "@/api/http";
import {
  listQuestions,
  createQuestion,
  updateQuestion,
  deleteQuestion,
  batchPublishQuestions,
  batchUnpublishQuestions,
  batchDisableQuestions,
  batchEnableQuestions,
  importQuestions,
  getQuestion,
  getQuestionNeighbors,
  batchDeleteQuestions,
  batchUpdateQuestionDifficulty,
} from "@/api/questions";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

type CourseOpt = {
  id: number;
  name: string;
  enterprise_id: number;
  enterprise?: { id: number; name: string };
};

const qTypeLabel: Record<string, string> = {
  judge: "判断",
  single: "单选",
  multiple: "多选",
  fill: "填空",
};
const statusLabel: Record<string, string> = {
  draft: "草稿",
  published: "已发布",
  disabled: "禁用",
};

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(50);
const lastImportLogText = ref("");
const filterType = ref<string | undefined>();
const filterStatus = ref<string | undefined>();
const filterCourseId = ref<number | undefined>();
const filterStem = ref("");
const selectedRows = ref<Record<string, unknown>[]>([]);

const toolbarCourseOpts = ref<{ id: number; label: string }[]>([]);
const toolbarCourseLoading = ref(false);

const formEntOpts = ref<{ id: number; name: string }[]>([]);
const formEntLoading = ref(false);
const formCourseOpts = ref<CourseOpt[]>([]);
const formCourseLoading = ref(false);

const importEntOpts = ref<{ id: number; name: string }[]>([]);
const importEntLoading = ref(false);
const importCourseOpts = ref<CourseOpt[]>([]);
const importCourseLoading = ref(false);

const dlg = ref(false);
const optionsText = ref("");
const answerText = ref("");
const form = reactive({
  id: 0,
  question_no: "",
  q_type: "single",
  stem: "",
  options_json: null as unknown,
  answer_json: null as unknown,
  analysis: "",
  difficulty: 1,
  status: "draft",
  course_id: null as number | null,
  enterprise_id: null as number | null,
});

const importDlg = ref(false);
const importEnterpriseId = ref<number | undefined>();
const importCourseId = ref<number | undefined>();
const importFiles = ref<File[]>([]);
const importLoading = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

const batchDifficultyDlg = ref(false);
const batchDifficultyValue = ref(1);
const batchDifficultyLoading = ref(false);
const batchDifficultyIds = ref<number[]>([]);

type ViewQuestionDetail = {
  id: number;
  question_no: string;
  q_type: string;
  stem: string;
  options_json: unknown;
  answer_json: unknown;
  analysis?: string | null;
  difficulty: number;
  status: string;
  course_name?: string | null;
  enterprise_name?: string | null;
};

type ViewNeighbors = {
  prev_id: number | null;
  next_id: number | null;
  index: number;
  total: number;
};

const viewDlg = ref(false);
const viewLoading = ref(false);
const viewDetail = ref<ViewQuestionDetail | null>(null);
const viewNav = ref<ViewNeighbors | null>(null);

function courseOptLabel(c: CourseOpt) {
  const en = c.enterprise?.name;
  return en ? `${c.name}（${en}）` : c.name;
}

function formatJsonField(v: unknown) {
  if (v == null) return "—";
  if (typeof v === "string") return v;
  return JSON.stringify(v, null, 2);
}

type ViewOptItem = { key?: string; text?: string };

function formatOptionsForView(opts: unknown): string {
  if (opts == null) return "—";
  if (!Array.isArray(opts)) return formatJsonField(opts);
  return (opts as ViewOptItem[])
    .map((o) => {
      const k = (o.key ?? "").trim();
      const t = (o.text ?? "").trim();
      return k ? `${k}. ${t}` : t;
    })
    .filter(Boolean)
    .join("\n");
}

function optionTextByKey(opts: unknown, key: string): string | null {
  if (!key || !Array.isArray(opts)) return null;
  const row = (opts as ViewOptItem[]).find((o) => String(o.key ?? "").toUpperCase() === key.toUpperCase());
  const t = row?.text;
  return t != null && String(t).trim() !== "" ? String(t).trim() : null;
}

function tryParseOptionsFromText(): unknown {
  const t = optionsText.value.trim();
  if (!t) return null;
  try {
    return JSON.parse(t);
  } catch {
    return null;
  }
}

function tryParseAnswerFromText(): unknown {
  const t = answerText.value.trim();
  if (!t) return null;
  try {
    if (t.startsWith("{") || t.startsWith("[")) return JSON.parse(t);
    return t;
  } catch {
    return null;
  }
}

const optionsPreview = computed(() => formatOptionsForView(tryParseOptionsFromText()));

const answerPreview = computed(() => {
  const ans = tryParseAnswerFromText();
  if (ans === null && !answerText.value.trim()) return "—";
  if (ans === null) return "（标准答案 JSON 无法解析，请检查格式）";
  return formatAnswerForView(ans, form.q_type, tryParseOptionsFromText());
});

function formatAnswerForView(ans: unknown, qType: string, options: unknown): string {
  if (ans == null) return "—";
  if (typeof ans === "string") return ans;
  if (typeof ans !== "object") return String(ans);
  const o = ans as Record<string, unknown>;
  if (qType === "judge") {
    const c = o.choice;
    if (c === "T" || c === true) return "正确";
    if (c === "F" || c === false) return "错误";
    return c != null ? String(c) : "—";
  }
  if (qType === "multiple") {
    const raw = o.choices;
    if (!Array.isArray(raw) || raw.length === 0) return formatJsonField(ans);
    const keys = raw.map((x) => String(x).toUpperCase());
    return keys
      .map((k) => {
        const label = optionTextByKey(options, k);
        return label ? `${k}（${label}）` : k;
      })
      .join("、");
  }
  if (qType === "fill") {
    const t = o.text;
    return t != null && String(t) !== "" ? String(t) : "—";
  }
  const k = o.choice != null ? String(o.choice).toUpperCase() : "";
  if (!k) return formatJsonField(ans);
  const label = optionTextByKey(options, k);
  return label ? `${k}（${label}）` : k;
}

function neighborQueryParams(): Record<string, unknown> {
  const p: Record<string, unknown> = {};
  if (filterCourseId.value != null) p.course_id = filterCourseId.value;
  if (filterType.value) p.q_type = filterType.value;
  if (filterStatus.value) p.status = filterStatus.value;
  const sk = filterStem.value.trim();
  if (sk) p.stem_keyword = sk;
  return p;
}

function resetView() {
  viewDetail.value = null;
  viewNav.value = null;
}

async function loadViewDetail(id: number) {
  viewLoading.value = true;
  try {
    const [{ data: d }, { data: n }] = await Promise.all([
      getQuestion(id),
      getQuestionNeighbors(id, neighborQueryParams()),
    ]);
    viewDetail.value = d as ViewQuestionDetail;
    viewNav.value = n as ViewNeighbors;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载失败"));
    viewDlg.value = false;
  } finally {
    viewLoading.value = false;
  }
}

async function openView(row: Record<string, unknown>) {
  viewDlg.value = true;
  await loadViewDetail(row.id as number);
}

async function gotoViewNeighbor(dir: "prev" | "next") {
  const id = dir === "prev" ? viewNav.value?.prev_id : viewNav.value?.next_id;
  if (id == null) return;
  await loadViewDetail(id);
}

async function remoteToolbarCourses(query: string) {
  toolbarCourseLoading.value = true;
  try {
    const { data } = await listCourses({
      skip: 0,
      limit: 50,
      keyword: query.trim() || undefined,
    });
    const items = (data.items || []) as CourseOpt[];
    toolbarCourseOpts.value = items.map((c) => ({
      id: c.id,
      label: courseOptLabel(c),
    }));
  } finally {
    toolbarCourseLoading.value = false;
  }
}

async function remoteFormEnterprises(query: string) {
  formEntLoading.value = true;
  try {
    const { data } = await listEnterprises({
      skip: 0,
      limit: 50,
      keyword: query.trim() || undefined,
    });
    formEntOpts.value = (data.items || []).map((e: { id: number; name: string }) => ({
      id: e.id,
      name: e.name,
    }));
  } finally {
    formEntLoading.value = false;
  }
}

async function remoteFormCourses(query: string) {
  if (!form.enterprise_id) {
    formCourseOpts.value = [];
    return;
  }
  formCourseLoading.value = true;
  try {
    const { data } = await listCourses({
      skip: 0,
      limit: 50,
      keyword: query.trim() || undefined,
      enterprise_id: auth.isAdmin ? form.enterprise_id : undefined,
    });
    formCourseOpts.value = (data.items || []) as CourseOpt[];
  } finally {
    formCourseLoading.value = false;
  }
}

async function remoteImportEnterprises(query: string) {
  importEntLoading.value = true;
  try {
    const { data } = await listEnterprises({
      skip: 0,
      limit: 50,
      keyword: query.trim() || undefined,
    });
    importEntOpts.value = (data.items || []).map((e: { id: number; name: string }) => ({
      id: e.id,
      name: e.name,
    }));
  } finally {
    importEntLoading.value = false;
  }
}

async function remoteImportCourses(query: string) {
  if (!importEnterpriseId.value) {
    importCourseOpts.value = [];
    return;
  }
  importCourseLoading.value = true;
  try {
    const { data } = await listCourses({
      skip: 0,
      limit: 50,
      keyword: query.trim() || undefined,
      enterprise_id: auth.isAdmin ? importEnterpriseId.value : undefined,
    });
    importCourseOpts.value = (data.items || []) as CourseOpt[];
  } finally {
    importCourseLoading.value = false;
  }
}

function mergeFormEnterprise(id: number | null, name: string | null | undefined) {
  if (!id || !name) return;
  if (!formEntOpts.value.some((e) => e.id === id)) {
    formEntOpts.value = [{ id, name }, ...formEntOpts.value];
  }
}

function mergeFormCourse(row: Record<string, unknown>) {
  const cid = row.course_id as number | null;
  const cname = row.course_name as string | null | undefined;
  const eid = row.enterprise_id as number | null;
  if (!cid || !cname) return;
  const ename = row.enterprise_name as string | undefined;
  if (!formCourseOpts.value.some((c) => c.id === cid)) {
    formCourseOpts.value = [
      {
        id: cid,
        name: cname,
        enterprise_id: eid ?? 0,
        enterprise: ename ? { id: eid ?? 0, name: ename } : undefined,
      },
      ...formCourseOpts.value,
    ];
  }
}

watch(optionsText, (v) => {
  if (!v.trim()) {
    form.options_json = null;
    return;
  }
  try {
    form.options_json = JSON.parse(v);
  } catch {
    /* 保存时再校验 */
  }
});
watch(answerText, (v) => {
  try {
    form.answer_json = JSON.parse(v);
  } catch {
    form.answer_json = v;
  }
});

function onFormEnterpriseChange() {
  const eid = form.enterprise_id;
  form.course_id = null;
  formCourseOpts.value = [];
  if (eid) void remoteFormCourses("");
}

function onSelectionChange(sel: Record<string, unknown>[]) {
  selectedRows.value = sel;
}

async function load() {
  const skip = (page.value - 1) * limit.value;
  const stem = filterStem.value.trim();
  const { data } = await listQuestions({
    skip,
    limit: limit.value,
    q_type: filterType.value,
    status: filterStatus.value,
    course_id: filterCourseId.value,
    stem_keyword: stem || undefined,
  });
  total.value = data.total;
  rows.value = data.items;
}

function doSearch() {
  page.value = 1;
  load();
}

function onPageSizeChange(s: number) {
  limit.value = s;
  page.value = 1;
  load();
}

function onPageChange(p: number) {
  page.value = p;
  load();
}

function downloadImportLog() {
  const t = lastImportLogText.value;
  if (!t) return;
  const blob = new Blob([t], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `题库导入日志_${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

async function openImport() {
  importEnterpriseId.value = auth.me?.enterprise_id ?? undefined;
  importCourseId.value = undefined;
  importFiles.value = [];
  if (fileInputRef.value) fileInputRef.value.value = "";
  importDlg.value = true;
  await remoteImportEnterprises("");
  const mid = importEnterpriseId.value;
  const mname = auth.me?.enterprise?.name;
  if (mid && mname && !importEntOpts.value.some((e) => e.id === mid)) {
    importEntOpts.value = [{ id: mid, name: mname }, ...importEntOpts.value];
  }
  if (importEnterpriseId.value) await remoteImportCourses("");
}

function resetImport() {
  importFiles.value = [];
  if (fileInputRef.value) fileInputRef.value.value = "";
}

function onImportFiles(ev: Event) {
  const t = ev.target as HTMLInputElement;
  importFiles.value = t.files?.length ? Array.from(t.files) : [];
}

async function submitImport() {
  if (!importCourseId.value || !importEnterpriseId.value || !importFiles.value.length) {
    ElMessage.warning("请选择所属企业、所属课程，并至少选择一个文件");
    return;
  }
  importLoading.value = true;
  try {
    const fd = new FormData();
    fd.append("course_id", String(importCourseId.value));
    fd.append("enterprise_id", String(importEnterpriseId.value));
    for (const f of importFiles.value) {
      fd.append("files", f);
    }
    const { data } = await importQuestions(fd);
    const d = data as {
      message?: string;
      log_text?: string;
      failed?: number;
    };
    lastImportLogText.value = d.log_text || "";
    if ((d.failed ?? 0) > 0) {
      ElMessage.warning(d.message || "导入完成，部分失败请查看日志");
    } else {
      ElMessage.success(d.message || "导入完成");
    }
    importDlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "导入失败"));
  } finally {
    importLoading.value = false;
  }
}

function onBatchDifficultyClosed() {
  batchDifficultyIds.value = [];
}

async function submitBatchDifficulty() {
  if (!batchDifficultyIds.value.length) {
    batchDifficultyDlg.value = false;
    return;
  }
  batchDifficultyLoading.value = true;
  try {
    const { data } = await batchUpdateQuestionDifficulty(batchDifficultyIds.value, batchDifficultyValue.value);
    const n = (data as { updated?: number }).updated ?? 0;
    ElMessage.success(`已更新 ${n} 道题目的难度系数`);
    batchDifficultyDlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "批量修改难度失败"));
  } finally {
    batchDifficultyLoading.value = false;
  }
}

async function onBatchCommand(cmd: string) {
  const ids = selectedRows.value.map((r) => r.id as number);
  if (!ids.length) return;
  if (cmd === "publish") {
    try {
      await ElMessageBox.confirm(`将选中的 ${ids.length} 道题目设为已发布？`, "批量发布", { type: "warning" });
      const { data } = await batchPublishQuestions(ids);
      const n = (data as { updated?: number }).updated ?? 0;
      ElMessage.success(`已发布 ${n} 道题目`);
      await load();
    } catch (e) {
      if (e !== "cancel") ElMessage.error("批量发布失败");
    }
    return;
  }
  if (cmd === "unpublish") {
    try {
      await ElMessageBox.confirm(
        `将选中的 ${ids.length} 道题目反发布为草稿？已发布题目删除前需先反发布。`,
        "批量反发布",
        { type: "warning" },
      );
      const { data } = await batchUnpublishQuestions(ids);
      const n = (data as { updated?: number }).updated ?? 0;
      ElMessage.success(`已反发布 ${n} 道题目`);
      await load();
    } catch (e) {
      if (e !== "cancel") ElMessage.error(apiErrorMessage(e, "批量反发布失败"));
    }
    return;
  }
  if (cmd === "disable") {
    try {
      await ElMessageBox.confirm(
        `将选中的 ${ids.length} 道已发布题目禁用？未发布题目不会变更；禁用后不可组卷、不可删除。`,
        "批量禁用",
        { type: "warning" },
      );
      const { data } = await batchDisableQuestions(ids);
      const n = (data as { updated?: number }).updated ?? 0;
      ElMessage.success(`已禁用 ${n} 道题目`);
      await load();
    } catch (e) {
      if (e !== "cancel") ElMessage.error(apiErrorMessage(e, "批量禁用失败"));
    }
    return;
  }
  if (cmd === "enable") {
    try {
      await ElMessageBox.confirm(
        `将选中的 ${ids.length} 道禁用题目反禁用为已发布？`,
        "批量反禁用",
        { type: "warning" },
      );
      const { data } = await batchEnableQuestions(ids);
      const n = (data as { updated?: number }).updated ?? 0;
      ElMessage.success(`已反禁用 ${n} 道题目`);
      await load();
    } catch (e) {
      if (e !== "cancel") ElMessage.error(apiErrorMessage(e, "批量反禁用失败"));
    }
    return;
  }
  if (cmd === "difficulty") {
    batchDifficultyIds.value = [...ids];
    batchDifficultyValue.value = 1;
    batchDifficultyDlg.value = true;
    return;
  }
  if (cmd === "delete") {
    try {
      await ElMessageBox.confirm(
        `确定删除选中的 ${ids.length} 道题目？删除后不可恢复。`,
        "批量删除",
        { type: "warning" },
      );
      const { data } = await batchDeleteQuestions(ids);
      const d = data as { deleted?: number; skipped?: number };
      const n = d.deleted ?? 0;
      const sk = d.skipped ?? 0;
      ElMessage.success(`已删除 ${n} 道题目${sk ? `，跳过 ${sk} 道（非草稿）` : ""}`);
      await load();
    } catch (e) {
      if (e !== "cancel") ElMessage.error(apiErrorMessage(e, "批量删除失败"));
    }
  }
}

async function openEdit(row?: Record<string, unknown>) {
  if (!row) {
    form.id = 0;
    form.question_no = "";
    form.q_type = "single";
    form.stem = "";
    form.analysis = "";
    form.difficulty = 1;
    form.status = "draft";
    form.enterprise_id = auth.me?.enterprise_id ?? null;
    form.course_id = null;
    optionsText.value = "";
    answerText.value = "";
    form.options_json = null;
    form.answer_json = null;
    formEntOpts.value = [];
    formCourseOpts.value = [];
    dlg.value = true;
    await remoteFormEnterprises("");
    if (form.enterprise_id) await remoteFormCourses("");
  } else {
    form.id = row.id as number;
    form.question_no = (row.question_no as string) || "";
    form.q_type = row.q_type as string;
    form.stem = row.stem as string;
    form.analysis = (row.analysis as string) || "";
    form.difficulty = row.difficulty as number;
    form.status = row.status as string;
    form.course_id = (row.course_id as number | null) ?? null;
    form.enterprise_id = (row.enterprise_id as number | null) ?? null;
    optionsText.value = row.options_json ? JSON.stringify(row.options_json, null, 2) : "";
    answerText.value =
      typeof row.answer_json === "string" ? row.answer_json : JSON.stringify(row.answer_json, null, 2);
    form.answer_json = row.answer_json;
    form.options_json = row.options_json;
    dlg.value = true;
    await remoteFormEnterprises("");
    mergeFormEnterprise(form.enterprise_id, row.enterprise_name as string);
    await remoteFormCourses("");
    mergeFormCourse(row);
  }
}

async function save() {
  try {
    if (optionsText.value.trim()) form.options_json = JSON.parse(optionsText.value);
    else form.options_json = null;
    if (answerText.value.trim().startsWith("{") || answerText.value.trim().startsWith("["))
      form.answer_json = JSON.parse(answerText.value);
    else form.answer_json = answerText.value;
  } catch {
    ElMessage.error("选项或答案 JSON 格式不正确");
    return;
  }
  const body = {
    q_type: form.q_type,
    stem: form.stem,
    options_json: form.options_json,
    answer_json: form.answer_json,
    analysis: form.analysis || null,
    difficulty: form.difficulty,
    status: form.status,
    course_id: form.course_id,
    enterprise_id: form.enterprise_id,
  };
  try {
    if (!form.id) await createQuestion(body);
    else await updateQuestion(form.id, body);
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

async function onDel(row: Record<string, unknown>) {
  if (row.status !== "draft") {
    ElMessage.warning("仅草稿可删除；已发布请先反发布，已禁用请先反禁用");
    return;
  }
  try {
    await ElMessageBox.confirm("确定删除？", "提示", { type: "warning" });
    await deleteQuestion(row.id as number);
    ElMessage.success("已删除");
    await load();
  } catch (e) {
    if (e !== "cancel") ElMessage.error(apiErrorMessage(e, "删除失败"));
  }
}

onMounted(async () => {
  await remoteToolbarCourses("");
  await load();
});
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.hint-text {
  margin: 6px 0 0;
  font-size: 12px;
  color: #64748b;
}
.view-meta {
  margin: 0 0 12px;
  font-size: 13px;
  color: #64748b;
}
.view-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 13px;
}
.view-body {
  min-height: 120px;
}
.readonly-preview :deep(.el-textarea__inner) {
  background: #f8fafc;
  cursor: default;
}
</style>
