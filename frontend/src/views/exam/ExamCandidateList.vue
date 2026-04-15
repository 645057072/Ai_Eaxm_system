<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title"><AppEmoji name="roleStudent" size="sm" decorative />考生管理</div>
      </template>

      <div class="page-list-toolbar toolbar">
        <el-select
          v-if="auth.isAdmin"
          v-model="filterEnterpriseId"
          clearable
          filterable
          placeholder="所属企业"
          style="width: 180px"
          @change="doSearch"
        >
          <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-input v-model="kwExamNo" clearable placeholder="考试编号" style="width: 160px" @keyup.enter="doSearch" />
        <el-button type="primary" @click="doSearch"><AppEmoji name="search" size="sm" decorative />查询</el-button>
        <el-button v-if="auth.can('action.exam_candidate.create')" type="success" @click="openCreate"
          ><AppEmoji name="add" size="sm" decorative />新建考生</el-button
        >
      </div>

      <div class="page-list-body">
        <div class="page-list-table">
          <el-table :data="rows" height="100%" style="width: 100%">
            <template #empty>
              <el-empty description="暂无考生数据" />
            </template>
            <el-table-column prop="exam_no" label="考试编号" width="140" show-overflow-tooltip />
            <el-table-column prop="enterprise_name" label="所属企业" min-width="140" show-overflow-tooltip />
            <el-table-column prop="course_name" label="课程" min-width="140" show-overflow-tooltip />
            <el-table-column label="学员" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">{{ formatStudentCell(row) }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="170">
              <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button v-if="auth.can('action.exam_candidate.update')" link type="primary" @click="openEdit(row)"
                  ><AppEmoji name="edit" size="sm" decorative />编辑</el-button
                >
                <el-button v-if="auth.can('action.exam_candidate.delete')" link type="danger" @click="onDelete(row)"
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
            :current-page="page"
            :page-sizes="[15, 50, 100, 200]"
            @current-change="onPagerPageChange"
            @size-change="onPageSizeChange"
          />
        </div>
      </div>
    </el-card>

    <el-dialog v-model="dlg" :title="editId ? '编辑考生' : '新建考生'" width="640px" @closed="onDlgClosed">
      <el-form label-width="100px">
        <el-form-item v-if="auth.isAdmin" label="所属企业" required>
          <el-select
            v-model="form.enterprise_id"
            clearable
            filterable
            placeholder="请选择企业"
            style="width: 100%"
            @change="onEnterpriseChange"
          >
            <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="考试编号" required>
          <el-input v-model="form.exam_no" placeholder="考试编号" />
        </el-form-item>
        <el-form-item label="课程" required>
          <el-select
            v-model="form.course_id"
            filterable
            clearable
            placeholder="请先选择企业"
            style="width: 100%"
            :disabled="!form.enterprise_id"
          >
            <el-option v-for="c in courseOpts" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学员" required>
          <el-select
            v-model="form.student_id"
            filterable
            remote
            reserve-keyword
            :remote-method="searchStudents"
            :loading="studentLoading"
            placeholder="编号/姓名检索"
            style="width: 100%"
            :disabled="!form.enterprise_id"
          >
            <el-option
              v-for="s in studentOpts"
              :key="s.id"
              :label="`${s.student_no} ${s.full_name}`"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editId" label="创建时间">
          <el-input :model-value="fmtTime(form.created_at)" disabled />
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
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import {
  listExamCandidates,
  createExamCandidate,
  patchExamCandidate,
  deleteExamCandidate,
  fetchExamCandidateStudentChoices,
} from "@/api/exam_candidates";
import { listEnterprises } from "@/api/enterprises";
import { listCourses } from "@/api/courses";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

type StuOpt = { id: number; student_no: string; full_name: string };
type CourseOpt = { id: number; name: string };

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(15);

const filterEnterpriseId = ref<number | undefined>();
const enterpriseOpts = ref<{ id: number; name: string }[]>([]);

const kwExamNo = ref("");

const dlg = ref(false);
const editId = ref<number | null>(null);
const studentLoading = ref(false);
const courseOpts = ref<CourseOpt[]>([]);
const studentOpts = ref<StuOpt[]>([]);

const form = reactive({
  enterprise_id: null as number | null,
  exam_no: "",
  course_id: null as number | null,
  student_id: null as number | null,
  created_at: "" as string,
});

function fmtTime(v: unknown) {
  if (!v) return "";
  return String(v).replace("T", " ").slice(0, 19);
}

function formatStudentCell(row: Record<string, unknown>) {
  const no = row.student_no as string | undefined;
  const nm = row.student_name as string | undefined;
  if (no && nm) return `${no} ${nm}`;
  if (nm) return nm;
  if (no) return no;
  return "—";
}

async function loadCourseOpts() {
  courseOpts.value = [];
  if (!form.enterprise_id) return;
  try {
    const { data } = await listCourses({
      skip: 0,
      limit: 500,
      enterprise_id: form.enterprise_id,
    });
    courseOpts.value = (data.items || []).map((it: { id: number; name: string }) => ({ id: it.id, name: it.name }));
  } catch {
    courseOpts.value = [];
  }
}

async function searchStudents(q: string) {
  if (!form.enterprise_id) {
    studentOpts.value = [];
    return;
  }
  studentLoading.value = true;
  try {
    const { data } = await fetchExamCandidateStudentChoices({
      enterprise_id: form.enterprise_id,
      keyword: q.trim() || undefined,
      limit: 50,
    });
    studentOpts.value = data.items || [];
  } catch (e) {
    studentOpts.value = [];
    ElMessage.error(apiErrorMessage(e, "加载学员失败"));
  } finally {
    studentLoading.value = false;
  }
}

function onEnterpriseChange() {
  form.course_id = null;
  form.student_id = null;
  courseOpts.value = [];
  studentOpts.value = [];
  void loadCourseOpts();
  void searchStudents("");
}

async function load() {
  const skip = (page.value - 1) * limit.value;
  const params: Record<string, unknown> = { skip, limit: limit.value };
  if (auth.isAdmin && filterEnterpriseId.value) params.enterprise_id = filterEnterpriseId.value;
  const a = kwExamNo.value.trim();
  if (a) params.exam_no_keyword = a;
  try {
    const { data } = await listExamCandidates(params);
    total.value = data.total;
    rows.value = data.items;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载失败"));
  }
}

function doSearch() {
  page.value = 1;
  void load();
}

function onPagerPageChange(p: number) {
  page.value = p;
  void load();
}

function onPageSizeChange(sz: number) {
  limit.value = sz;
  page.value = 1;
  void load();
}

function openCreate() {
  editId.value = null;
  form.enterprise_id = auth.isAdmin ? enterpriseOpts.value[0]?.id ?? null : auth.me?.enterprise_id ?? null;
  form.exam_no = "";
  form.course_id = null;
  form.student_id = null;
  form.created_at = "";
  dlg.value = true;
  void loadCourseOpts();
  void searchStudents("");
}

function openEdit(row: Record<string, unknown>) {
  editId.value = row.id as number;
  form.enterprise_id = (row.enterprise_id as number) ?? null;
  form.exam_no = (row.exam_no as string) || "";
  form.course_id = (row.course_id as number) ?? null;
  form.student_id = (row.student_id as number) ?? null;
  form.created_at = (row.created_at as string) || "";
  studentOpts.value = [
    {
      id: row.student_id as number,
      student_no: (row.student_no as string) || "",
      full_name: (row.student_name as string) || "",
    },
  ];
  dlg.value = true;
  void loadCourseOpts();
}

function onDlgClosed() {
  editId.value = null;
}

async function save() {
  if (!form.exam_no.trim()) return ElMessage.warning("请填写考试编号");
  if (!form.enterprise_id) return ElMessage.warning("请选择所属企业");
  if (!form.course_id) return ElMessage.warning("请选择课程");
  if (!form.student_id) return ElMessage.warning("请选择学员");
  const body: Record<string, unknown> = {
    exam_no: form.exam_no.trim(),
    course_id: form.course_id,
    student_id: form.student_id,
  };
  if (auth.isAdmin) body.enterprise_id = form.enterprise_id;
  try {
    if (!editId.value) await createExamCandidate(body);
    else await patchExamCandidate(editId.value, body);
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

async function onDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm("确定删除该考生记录？", "提示", { type: "warning" });
  try {
    await deleteExamCandidate(row.id as number);
    ElMessage.success("已删除");
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "删除失败"));
  }
}

const suppressFilterWatch = ref(true);
let filterDebounce: ReturnType<typeof setTimeout> | null = null;
watch([kwExamNo], () => {
  if (suppressFilterWatch.value) return;
  if (filterDebounce) clearTimeout(filterDebounce);
  filterDebounce = setTimeout(() => {
    filterDebounce = null;
    doSearch();
  }, 400);
});

watch(
  () => dlg.value,
  (open) => {
    if (open && !editId.value && !auth.isAdmin && auth.me?.enterprise_id) {
      form.enterprise_id = auth.me.enterprise_id;
      void loadCourseOpts();
      void searchStudents("");
    }
  },
);

onMounted(async () => {
  if (auth.isAdmin) {
    try {
      const { data } = await listEnterprises({ skip: 0, limit: 500 });
      enterpriseOpts.value = (data.items || []).map((x: { id: number; name: string }) => ({ id: x.id, name: x.name }));
    } catch {
      enterpriseOpts.value = [];
    }
  }
  suppressFilterWatch.value = false;
  await load();
});
</script>

<style scoped>
.toolbar {
  flex-wrap: wrap;
  gap: 8px;
}
</style>
