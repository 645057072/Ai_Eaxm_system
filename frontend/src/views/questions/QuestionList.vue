<template>
  <el-card>
    <div class="toolbar">
      <el-select v-model="filterType" clearable placeholder="题型" style="width: 140px">
        <el-option label="判断" value="judge" />
        <el-option label="单选" value="single" />
        <el-option label="多选" value="multiple" />
        <el-option label="填空" value="fill" />
      </el-select>
      <el-select v-model="filterStatus" clearable placeholder="状态" style="width: 140px">
        <el-option label="草稿" value="draft" />
        <el-option label="已发布" value="published" />
      </el-select>
      <el-select v-model="filterCourseId" clearable placeholder="课程" filterable style="width: 200px">
        <el-option v-for="c in courseOptions" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-button type="primary" @click="load"><AppEmoji name="search" size="sm" decorative />查询</el-button>
      <el-button type="success" @click="openEdit()"><AppEmoji name="add" size="sm" decorative />新建题目</el-button>
      <el-button v-if="auth.can('action.question.import')" type="warning" @click="openImport">导入题库</el-button>
      <el-dropdown v-if="auth.can('action.question.batch')" trigger="click" @command="onBatchCommand">
        <el-button type="primary" :disabled="!selectedRows.length">
          批量操作<el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="publish">发布</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
    <el-table :data="rows" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="48" />
      <el-table-column prop="id" label="ID" width="70" />
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
      <el-table-column label="状态" width="90">
        <template #default="{ row }">{{ statusLabel[row.status as string] ?? row.status }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)"><AppEmoji name="edit" size="sm" decorative />编辑</el-button>
          <el-button link type="danger" @click="onDel(row)"><AppEmoji name="delete" size="sm" decorative />删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pager">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="limit"
        @current-change="(p: number) => { page = p; load(); }"
      />
    </div>

    <el-dialog v-model="dlg" :title="form.id ? '编辑题目' : '新建题目'" width="640px">
      <el-form label-width="100px">
        <el-form-item label="所属企业">
          <el-select v-model="form.enterprise_id" clearable placeholder="请选择" style="width: 100%" @change="onFormEnterpriseChange">
            <el-option v-for="e in enterpriseOptions" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属课程">
          <el-select v-model="form.course_id" clearable placeholder="请选择" style="width: 100%" filterable>
            <el-option v-for="c in coursesForForm" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="题型">
          <el-select v-model="form.q_type" style="width: 100%">
            <el-option label="判断 judge" value="judge" />
            <el-option label="单选 single" value="single" />
            <el-option label="多选 multiple" value="multiple" />
            <el-option label="填空 fill" value="fill" />
          </el-select>
        </el-form-item>
        <el-form-item label="题干"><el-input v-model="form.stem" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="选项 JSON"
          ><el-input v-model="optionsText" type="textarea" :rows="4" placeholder='如 [{"key":"A","text":"..."}]'
        /></el-form-item>
        <el-form-item label="答案 JSON"
          ><el-input v-model="answerText" type="textarea" :rows="3" placeholder="见详设说明"
        /></el-form-item>
        <el-form-item label="解析"><el-input v-model="form.analysis" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="难度(1-5)"><el-input-number v-model="form.difficulty" :min="1" :max="5" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="草稿 draft" value="draft" />
            <el-option label="已发布 published" value="published" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDlg" title="导入题库" width="520px" @closed="resetImport">
      <el-form label-width="100px">
        <el-form-item label="所属企业" required>
          <el-select v-model="importEnterpriseId" placeholder="请选择" style="width: 100%" @change="importCourseId = undefined">
            <el-option v-for="e in enterpriseOptions" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属课程" required>
          <el-select v-model="importCourseId" placeholder="请选择" style="width: 100%" filterable :disabled="!importEnterpriseId">
            <el-option v-for="c in coursesForImport" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="导入文件" required>
          <input
            ref="fileInputRef"
            type="file"
            accept=".doc,.docx,.xls,.xlsx,.pdf,.txt,.csv,.png,.jpg,.jpeg,.gif,.webp,.bmp"
            @change="onImportFile"
          />
          <p class="hint-text">支持 Word、Excel、PDF、图片、txt、CSV 等格式。</p>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDlg = false">取消</el-button>
        <el-button type="primary" :loading="importLoading" @click="submitImport">开始导入</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ArrowDown } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { listCourses } from "@/api/courses";
import { listEnterprises } from "@/api/enterprises";
import {
  listQuestions,
  createQuestion,
  updateQuestion,
  deleteQuestion,
  batchPublishQuestions,
  importQuestions,
} from "@/api/questions";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const qTypeLabel: Record<string, string> = {
  judge: "判断",
  single: "单选",
  multiple: "多选",
  fill: "填空",
};
const statusLabel: Record<string, string> = {
  draft: "草稿",
  published: "已发布",
};

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const filterType = ref<string | undefined>();
const filterStatus = ref<string | undefined>();
const filterCourseId = ref<number | undefined>();
const selectedRows = ref<Record<string, unknown>[]>([]);

type Opt = { id: number; name: string; enterprise_id?: number };
const courseOptions = ref<Opt[]>([]);
const enterpriseOptions = ref<Opt[]>([]);

const dlg = ref(false);
const optionsText = ref("");
const answerText = ref("");
const form = reactive({
  id: 0,
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
const importFile = ref<File | null>(null);
const importLoading = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

const coursesForImport = computed(() => {
  if (!importEnterpriseId.value) return [];
  return courseOptions.value.filter((c) => c.enterprise_id === importEnterpriseId.value);
});

const coursesForForm = computed(() => {
  if (!form.enterprise_id) return courseOptions.value;
  return courseOptions.value.filter((c) => c.enterprise_id === form.enterprise_id);
});

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
  if (form.course_id && eid) {
    const c = courseOptions.value.find((x) => x.id === form.course_id);
    if (c && c.enterprise_id !== eid) form.course_id = null;
  }
}

function onSelectionChange(sel: Record<string, unknown>[]) {
  selectedRows.value = sel;
}

async function loadRef() {
  const [ce, en] = await Promise.all([
    listCourses({ skip: 0, limit: 500 }),
    listEnterprises({ skip: 0, limit: 500 }),
  ]);
  const items = (ce.data.items || []) as { id: number; name: string; enterprise_id: number }[];
  courseOptions.value = items.map((c) => ({ id: c.id, name: c.name, enterprise_id: c.enterprise_id }));
  enterpriseOptions.value = ((en.data.items || []) as { id: number; name: string }[]).map((e) => ({
    id: e.id,
    name: e.name,
  }));
}

async function load() {
  const skip = (page.value - 1) * limit.value;
  const { data } = await listQuestions({
    skip,
    limit: limit.value,
    q_type: filterType.value,
    status: filterStatus.value,
    course_id: filterCourseId.value,
  });
  total.value = data.total;
  rows.value = data.items;
}

function openImport() {
  importEnterpriseId.value = auth.me?.enterprise_id ?? undefined;
  importCourseId.value = undefined;
  importFile.value = null;
  if (fileInputRef.value) fileInputRef.value.value = "";
  importDlg.value = true;
}

function resetImport() {
  importFile.value = null;
  if (fileInputRef.value) fileInputRef.value.value = "";
}

function onImportFile(ev: Event) {
  const t = ev.target as HTMLInputElement;
  const f = t.files?.[0];
  importFile.value = f ?? null;
}

async function submitImport() {
  if (!importCourseId.value || !importEnterpriseId.value || !importFile.value) {
    ElMessage.warning("请选择所属企业、所属课程与导入文件");
    return;
  }
  importLoading.value = true;
  try {
    const fd = new FormData();
    fd.append("course_id", String(importCourseId.value));
    fd.append("enterprise_id", String(importEnterpriseId.value));
    fd.append("file", importFile.value);
    const { data } = await importQuestions(fd);
    ElMessage.success((data as { message?: string }).message || "导入完成");
    importDlg.value = false;
    await load();
  } catch {
    ElMessage.error("导入失败");
  } finally {
    importLoading.value = false;
  }
}

async function onBatchCommand(cmd: string) {
  if (cmd !== "publish") return;
  const ids = selectedRows.value.map((r) => r.id as number);
  if (!ids.length) return;
  try {
    await ElMessageBox.confirm(`将选中的 ${ids.length} 道题目设为已发布？`, "批量发布", { type: "warning" });
    const { data } = await batchPublishQuestions(ids);
    const n = (data as { updated?: number }).updated ?? 0;
    ElMessage.success(`已发布 ${n} 道题目`);
    await load();
  } catch (e) {
    if (e !== "cancel") ElMessage.error("批量发布失败");
  }
}

function openEdit(row?: Record<string, unknown>) {
  if (!row) {
    form.id = 0;
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
  } else {
    form.id = row.id as number;
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
  }
  dlg.value = true;
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
  } catch {
    ElMessage.error("保存失败");
  }
}

async function onDel(row: Record<string, unknown>) {
  await ElMessageBox.confirm("确定删除？", "提示", { type: "warning" });
  await deleteQuestion(row.id as number);
  ElMessage.success("已删除");
  await load();
}

onMounted(async () => {
  await loadRef();
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
</style>
