<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title">打印设置</div>
      </template>
      <div class="page-list-toolbar toolbar">
        <el-select
          v-model="filterCourseId"
          clearable
          placeholder="筛选课程"
          filterable
          style="width: 260px"
          @change="doSearch"
        >
          <el-option v-for="c in courseOpts" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button type="primary" @click="doSearch">查询</el-button>
        <el-button v-if="auth.can('action.print_template.manage')" type="success" @click="openCreate">新建模板</el-button>
      </div>
      <div class="page-list-body">
        <div class="page-list-table">
          <el-table :data="rows" height="100%">
            <el-table-column prop="template_no" label="模板编号" width="120" show-overflow-tooltip />
            <el-table-column prop="template_name" label="模板名称" min-width="100" show-overflow-tooltip />
            <el-table-column prop="module_code" label="模块" width="120" show-overflow-tooltip />
            <el-table-column prop="menu_code" label="菜单" min-width="140" show-overflow-tooltip />
            <el-table-column label="课程" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">{{ (row.course_name as string) || "—" }}</template>
            </el-table-column>
            <el-table-column prop="paper_format" label="格式" width="72" />
            <el-table-column label="发布范围" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">
                <span v-if="row.status !== 'published'">—</span>
                <span v-else-if="row.publish_scope_enterprise_id == null">全局可用</span>
                <span v-else>{{ (row.publish_scope_enterprise_name as string) || "指定企业" }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="88" />
            <el-table-column v-if="auth.can('action.print_template.manage')" label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="goDesign(row)">设计</el-button>
                <el-button link type="warning" @click="onReset(row)">重置</el-button>
                <el-button link type="success" @click="openPublish(row)">发布</el-button>
                <el-button link type="danger" @click="onDelete(row)">删除</el-button>
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

    <el-dialog v-model="dlg" title="打印模板" width="560px">
      <el-form label-width="110px">
        <el-form-item label="模板编号" required>
          <el-input v-model="form.template_no" :disabled="!!form.id" placeholder="全系统唯一" />
        </el-form-item>
        <el-form-item label="模板名称">
          <el-input v-model="form.template_name" placeholder="选填" />
        </el-form-item>
        <el-form-item label="模块" required>
          <el-select v-model="form.module_code" placeholder="业务模块" style="width: 100%">
            <el-option v-for="o in moduleOpts" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="菜单" required>
          <el-select v-model="form.menu_code" placeholder="关联菜单功能点" filterable style="width: 100%">
            <el-option v-for="o in menuOpts" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程" required>
          <el-select v-model="form.course_id" placeholder="关联课程" filterable style="width: 100%">
            <el-option v-for="c in courseOpts" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="纸张格式" required>
          <el-select v-model="form.paper_format" style="width: 100%">
            <el-option label="A4" value="A4" />
            <el-option label="A3" value="A3" />
            <el-option label="B5" value="B5" />
            <el-option label="自定义(默认A4尺寸)" value="CUSTOM" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="saveForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pubDlg" title="发布打印模板" width="480px">
      <p class="pub-hint">不选企业则发布后全系统可用；选择企业则仅该企业范围内可用。</p>
      <el-form label-width="100px">
        <el-form-item label="所属企业">
          <el-select v-model="publishEnterpriseId" clearable placeholder="不选=全局" filterable style="width: 100%">
            <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pubDlg = false">取消</el-button>
        <el-button type="primary" @click="confirmPublish">确定发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import {
  listPrintTemplates,
  createPrintTemplate,
  updatePrintTemplate,
  resetPrintTemplate,
  publishPrintTemplate,
  deletePrintTemplate,
} from "@/api/print_templates";
import { listCourses } from "@/api/courses";
import { listEnterprises } from "@/api/enterprises";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const filterCourseId = ref<number | undefined>(undefined);
const courseOpts = ref<{ id: number; name: string }[]>([]);
const enterpriseOpts = ref<{ id: number; name: string }[]>([]);

const dlg = ref(false);
const pubDlg = ref(false);
const publishRow = ref<Record<string, unknown> | null>(null);
const publishEnterpriseId = ref<number | undefined>(undefined);

const moduleOpts = [
  { value: "paper_archive", label: "试卷档案" },
  { value: "exam_session", label: "考试场次" },
  { value: "qb_center", label: "题库中心" },
];

const menuOpts = [
  { value: "menu.exam.paper_manage", label: "试卷管理" },
  { value: "menu.exam.paper_publish", label: "场次发布" },
  { value: "menu.exam.sessions", label: "考试场次" },
  { value: "menu.exam.question_manage", label: "题库管理" },
  { value: "menu.system.print", label: "打印设置" },
];

const form = reactive({
  id: 0,
  template_no: "",
  template_name: "",
  module_code: "paper_archive",
  menu_code: "menu.exam.paper_manage",
  course_id: null as number | null,
  paper_format: "A4",
});

async function loadCourses() {
  const { data } = await listCourses({ skip: 0, limit: 500 });
  courseOpts.value = (data.items || []).map((x: { id: number; name: string }) => ({ id: x.id, name: x.name }));
}

async function loadEnterprises() {
  const { data } = await listEnterprises({ skip: 0, limit: 500 });
  enterpriseOpts.value = (data.items || []).map((x: { id: number; name: string }) => ({ id: x.id, name: x.name }));
}

function doSearch() {
  page.value = 1;
  void load();
}

async function load() {
  try {
    const skip = (page.value - 1) * limit.value;
    const params: Record<string, unknown> = { skip, limit: limit.value };
    if (filterCourseId.value) params.course_id = filterCourseId.value;
    const { data } = await listPrintTemplates(params);
    total.value = data.total;
    rows.value = data.items;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载失败"));
  }
}

function openCreate() {
  form.id = 0;
  form.template_no = "";
  form.template_name = "";
  form.module_code = "paper_archive";
  form.menu_code = "menu.exam.paper_manage";
  form.course_id = filterCourseId.value ?? courseOpts.value[0]?.id ?? null;
  form.paper_format = "A4";
  dlg.value = true;
}

async function saveForm() {
  if (!form.template_no.trim() || !form.course_id) {
    ElMessage.warning("请填写模板编号与课程");
    return;
  }
  const body: Record<string, unknown> = {
    template_no: form.template_no.trim(),
    template_name: form.template_name.trim(),
    module_code: form.module_code,
    menu_code: form.menu_code,
    course_id: form.course_id,
    paper_format: form.paper_format,
  };
  try {
    if (!form.id) await createPrintTemplate(body);
    else await updatePrintTemplate(form.id, body);
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

function goDesign(row: Record<string, unknown>) {
  router.push({ name: "print-template-design", params: { id: String(row.id) } });
}

async function onReset(row: Record<string, unknown>) {
  try {
    await ElMessageBox.confirm("将版式恢复为当前纸张规格下的默认样式，是否继续？", "重置确认", { type: "warning" });
  } catch {
    return;
  }
  try {
    await resetPrintTemplate(row.id as number);
    ElMessage.success("已重置");
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "重置失败"));
  }
}

function openPublish(row: Record<string, unknown>) {
  publishRow.value = row;
  publishEnterpriseId.value = undefined;
  pubDlg.value = true;
}

async function confirmPublish() {
  if (!publishRow.value) return;
  try {
    await publishPrintTemplate(publishRow.value.id as number, {
      enterprise_id: publishEnterpriseId.value ?? null,
    });
    ElMessage.success("已发布");
    pubDlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "发布失败"));
  }
}

async function onDelete(row: Record<string, unknown>) {
  try {
    await ElMessageBox.confirm(`确定删除模板「${row.template_no}」？`, "删除确认", { type: "warning" });
  } catch {
    return;
  }
  try {
    await deletePrintTemplate(row.id as number);
    ElMessage.success("已删除");
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "删除失败"));
  }
}

onMounted(async () => {
  const q = route.query.course_id;
  if (q != null && q !== "") {
    const n = Number(q);
    if (!Number.isNaN(n)) filterCourseId.value = n;
  }
  await loadCourses();
  if (auth.can("action.print_template.manage")) await loadEnterprises();
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
.pub-hint {
  margin: 0 0 12px;
  color: #666;
  font-size: 13px;
}
</style>
