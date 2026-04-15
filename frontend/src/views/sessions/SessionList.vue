<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title">考试场次</div>
      </template>
      <div class="page-list-toolbar toolbar">
        <el-input
          v-model="filterEnterpriseKw"
          clearable
          placeholder="所属企业"
          style="width: 150px"
          @keyup.enter="doSearch"
        />
        <el-input
          v-model="filterCourseKw"
          clearable
          placeholder="课程"
          style="width: 130px"
          @keyup.enter="doSearch"
        />
        <el-button type="primary" @click="doSearch">查询</el-button>
        <el-button type="success" @click="openCreate">新建场次</el-button>
        <el-dropdown v-if="auth.can('action.session.manage')" trigger="click" @command="onBatchCommand">
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
            <el-table-column prop="session_code" label="场次编码" width="120" show-overflow-tooltip />
            <el-table-column label="所属企业" min-width="140" show-overflow-tooltip>
              <template #default="{ row }">{{ (row.enterprise_name as string) || "—" }}</template>
            </el-table-column>
            <el-table-column label="课程" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">{{ (row.course_name as string) || "—" }}</template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="120" show-overflow-tooltip />
            <el-table-column label="试卷编号" width="130" show-overflow-tooltip>
              <template #default="{ row }">{{ (row.paper_no as string) || "—" }}</template>
            </el-table-column>
            <el-table-column label="状态" width="200">
              <template #default="{ row }">
                <div class="status-cell">
                  <el-tag size="small" :type="statusTagType(row.status as string)">{{ statusText(row.status as string) }}</el-tag>
                  <el-tag size="small" :type="publishBadgeType(row.status as string)">{{ publishBadgeText(row.status as string) }}</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="开始" width="170">
              <template #default="{ row }">{{ fmt(row.start_at) }}</template>
            </el-table-column>
            <el-table-column label="结束" width="170">
              <template #default="{ row }">{{ fmt(row.end_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="260" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
                <template v-if="auth.can('action.session.manage')">
                  <el-button v-if="row.status !== 'published'" link type="success" @click="publish(row)">发布</el-button>
                  <el-button v-if="row.status === 'published'" link type="warning" @click="unpublish(row)">反发布</el-button>
                  <el-button link type="danger" @click="removeOne(row)">删除</el-button>
                </template>
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

    <el-dialog v-model="dlg" :title="form.id ? '编辑场次' : '新建场次'" width="560px">
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
          >
            <el-option v-for="p in paperOpts" :key="p.id" :label="paperOptLabel(p)" :value="p.id" />
          </el-select>
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
import { onMounted, reactive, ref } from "vue";
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
import { listPapers } from "@/api/papers";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const dlg = ref(false);
const filterEnterpriseKw = ref("");
const filterCourseKw = ref("");
const selectedRows = ref<Record<string, unknown>[]>([]);

const enterpriseOpts = ref<{ id: number; name: string }[]>([]);
const courseOpts = ref<{ id: number; name: string }[]>([]);
const paperOpts = ref<{ id: number; title: string; paper_no?: string | null; course_id?: number | null }[]>([]);

const form = reactive({
  id: 0,
  session_code: "",
  enterprise_id: null as number | null,
  course_id: null as number | null,
  paper_id: null as number | null,
  title: "",
  start_at: "" as string | undefined,
  end_at: "" as string | undefined,
});

function fmt(v: unknown) {
  if (!v) return "";
  return String(v).replace("T", " ").slice(0, 19);
}

/** 业务状态：草稿与已发布均视为编辑态，仅已结束单独展示 */
function statusText(status: string) {
  if (status === "closed") return "已结束";
  return "草稿";
}

function statusTagType(status: string): "warning" | "info" {
  if (status === "closed") return "warning";
  return "info";
}

/** 发布标识：与「草稿」状态并存；发布后标签保留不消失 */
function publishBadgeText(status: string) {
  if (status === "published") return "已发布";
  return "未发布";
}

function publishBadgeType(status: string): "success" | "info" {
  return status === "published" ? "success" : "info";
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
    (x: { id: number; title: string; paper_no?: string | null; course_id?: number | null }) => ({
      id: x.id,
      title: x.title,
      paper_no: x.paper_no,
      course_id: x.course_id,
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
    const ek = filterEnterpriseKw.value.trim();
    const ck = filterCourseKw.value.trim();
    if (ek) params.enterprise_keyword = ek;
    if (ck) params.course_keyword = ck;
    const { data } = await listSessions(params);
    total.value = data.total;
    rows.value = data.items;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载场次失败"));
  }
}

async function openCreate() {
  form.id = 0;
  form.session_code = "";
  form.title = "";
  form.start_at = undefined;
  form.end_at = undefined;
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
  form.id = row.id as number;
  form.session_code = (row.session_code as string) || "";
  form.title = (row.title as string) || "";
  form.start_at = row.start_at as string | undefined;
  form.end_at = row.end_at as string | undefined;
  form.enterprise_id = (row.enterprise_id as number) || null;
  form.course_id = (row.course_id as number) || null;
  form.paper_id = (row.paper_id as number) || null;
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
      });
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

async function publish(row: Record<string, unknown>) {
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

async function onBatchCommand(cmd: string) {
  const sel = selectedRows.value;
  if (!sel.length) return;
  if (cmd === "publish") {
    const targets = sel.filter((r) => r.status !== "published");
    if (!targets.length) {
      ElMessage.info("所选行均已发布");
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
    try {
      await ElMessageBox.confirm(`确定删除选中的 ${sel.length} 条场次？`, "批量删除", { type: "warning" });
    } catch {
      return;
    }
    try {
      for (const r of sel) {
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
.status-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
</style>
