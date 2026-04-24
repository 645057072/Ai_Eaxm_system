<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title"><AppEmoji name="certificate" size="sm" decorative />证书管理</div>
      </template>
      <el-tabs v-model="activeTab" class="cert-tabs">
        <el-tab-pane label="证书模板" name="tpl">
          <div class="page-list-toolbar toolbar">
            <el-input
              v-model="tplKeyword"
              clearable
              placeholder="模板编码 / 名称"
              style="width: 260px"
              @keyup.enter="searchTpl"
            />
            <el-button type="primary" @click="searchTpl">查询</el-button>
            <el-button v-if="auth.can('action.cert_template.manage')" type="success" @click="openTplCreate">新建模板</el-button>
          </div>
          <div class="page-list-body">
            <div class="page-list-table">
              <el-table :data="tplRows" height="100%" style="width: 100%">
                <template #empty>
                  <el-empty description="暂无证书模板" />
                </template>
                <el-table-column prop="cert_code" label="模板编码" width="130" show-overflow-tooltip />
                <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
                <el-table-column label="关联课程" min-width="120" show-overflow-tooltip>
                  <template #default="{ row }">{{ (row.course_name as string) || "通用" }}</template>
                </el-table-column>
                <el-table-column prop="enterprise_name" label="所属企业" min-width="120" show-overflow-tooltip />
                <el-table-column label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">{{
                      row.status === "published" ? "已发布" : "草稿"
                    }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="更新时间" width="170">
                  <template #default="{ row }">{{ fmtTime(row.updated_at) }}</template>
                </el-table-column>
                <el-table-column
                  v-if="auth.can('action.cert_template.manage')"
                  label="操作"
                  width="160"
                  fixed="right"
                >
                  <template #default="{ row }">
                    <el-button link type="primary" @click="openTplEdit(row)">编辑</el-button>
                    <el-button link type="danger" @click="onTplDelete(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div class="page-list-pager">
              <el-pagination
                background
                layout="total, sizes, prev, pager, next"
                :total="tplTotal"
                :page-size="tplLimit"
                :current-page="tplPage"
                :page-sizes="[15, 50, 100]"
                @current-change="onTplPage"
                @size-change="onTplSize"
              />
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="颁发记录" name="rec">
          <div class="page-list-toolbar toolbar">
            <el-input
              v-model="recKeyword"
              clearable
              placeholder="证书编号 / 学员 / 课程 / 模板"
              style="width: 300px"
              @keyup.enter="searchRec"
            />
            <el-button type="primary" @click="searchRec">查询</el-button>
            <el-button v-if="auth.can('action.cert_record.issue')" type="success" @click="openIssue">颁发证书</el-button>
          </div>
          <div class="page-list-body">
            <div class="page-list-table">
              <el-table :data="recRows" height="100%" style="width: 100%">
                <template #empty>
                  <el-empty description="暂无颁发记录" />
                </template>
                <el-table-column prop="certificate_no" label="证书编号" width="180" show-overflow-tooltip />
                <el-table-column prop="template_name" label="模板名称" min-width="120" show-overflow-tooltip />
                <el-table-column prop="cert_code" label="模板编码" width="120" show-overflow-tooltip />
                <el-table-column prop="student_display" label="学员" min-width="120" show-overflow-tooltip />
                <el-table-column prop="course_name" label="课程" min-width="120" show-overflow-tooltip />
                <el-table-column prop="exam_no" label="考试编号" width="120" show-overflow-tooltip />
                <el-table-column label="得分" width="88" align="right">
                  <template #default="{ row }">{{ row.score }}</template>
                </el-table-column>
                <el-table-column label="颁发时间" width="170">
                  <template #default="{ row }">{{ fmtTime(row.issued_at) }}</template>
                </el-table-column>
              </el-table>
            </div>
            <div class="page-list-pager">
              <el-pagination
                background
                layout="total, sizes, prev, pager, next"
                :total="recTotal"
                :page-size="recLimit"
                :current-page="recPage"
                :page-sizes="[15, 50, 100]"
                @current-change="onRecPage"
                @size-change="onRecSize"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="tplDialog" :title="tplEditId ? '编辑证书模板' : '新建证书模板'" width="640px" destroy-on-close>
      <el-form ref="tplFormRef" :model="tplForm" label-width="100px">
        <el-form-item v-if="auth.isAdmin" label="所属企业" required>
          <el-select v-model="tplForm.enterprise_id" placeholder="请选择企业" filterable style="width: 100%" @change="onTplEnterpriseChange">
            <el-option v-for="e in enterpriseOptions" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板编码" required>
          <el-input v-model="tplForm.cert_code" :disabled="!!tplEditId" placeholder="英文字母、数字、下划线" maxlength="64" />
        </el-form-item>
        <el-form-item label="模板名称">
          <el-input v-model="tplForm.name" maxlength="200" />
        </el-form-item>
        <el-form-item label="关联课程">
          <el-select v-model="tplForm.course_id" clearable placeholder="不选表示全课程通用" filterable style="width: 100%">
            <el-option v-for="c in courseOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="tplForm.status">
            <el-radio :value="'draft'">草稿</el-radio>
            <el-radio :value="'published'">已发布</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="版式 JSON">
          <el-input v-model="tplForm.layout_json_str" type="textarea" :rows="8" placeholder="可留空使用默认版式；须为合法 JSON" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tplDialog = false">取消</el-button>
        <el-button type="primary" @click="submitTpl">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="issueDialog" title="颁发证书" width="520px" destroy-on-close @open="loadIssueOptions">
      <el-form label-width="120px">
        <el-form-item label="证书模板" required>
          <el-select v-model="issueForm.cert_template_id" placeholder="请选择已发布模板" filterable style="width: 100%">
            <el-option
              v-for="t in issueTemplateOptions"
              :key="t.id"
              :label="`${t.cert_code} — ${t.name}`"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="考试服务记录" required>
          <el-select
            v-model="issueForm.exam_service_record_id"
            placeholder="请选择已通过记录"
            filterable
            style="width: 100%"
          >
            <el-option v-for="r in passedRecordOptions" :key="r.id" :label="issueRecordLabel(r)" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label=" ">
          <el-checkbox v-model="issueForm.require_passed">仅允许已通过记录（推荐）</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="issueDialog = false">取消</el-button>
        <el-button type="primary" @click="submitIssue">确定颁发</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import {
  listCertTemplates,
  createCertTemplate,
  patchCertTemplate,
  deleteCertTemplate,
  listCertRecords,
  issueCertRecord,
} from "@/api/certificates";
import { listCourses } from "@/api/courses";
import { listEnterprises } from "@/api/enterprises";
import { listExamServiceRecords } from "@/api/exam_service_records";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const activeTab = ref("tpl");

const tplRows = ref<Record<string, unknown>[]>([]);
const tplTotal = ref(0);
const tplPage = ref(1);
const tplLimit = ref(15);
const tplKeyword = ref("");

const recRows = ref<Record<string, unknown>[]>([]);
const recTotal = ref(0);
const recPage = ref(1);
const recLimit = ref(15);
const recKeyword = ref("");

const tplDialog = ref(false);
const tplEditId = ref<number | null>(null);
const tplForm = ref({
  enterprise_id: null as number | null,
  cert_code: "",
  name: "",
  course_id: null as number | null,
  status: "draft",
  layout_json_str: "",
});
const enterpriseOptions = ref<{ id: number; name: string }[]>([]);
const courseOptions = ref<{ id: number; name: string }[]>([]);

const issueDialog = ref(false);
const issueForm = ref({
  cert_template_id: null as number | null,
  exam_service_record_id: null as number | null,
  require_passed: true,
});
const issueTemplateOptions = ref<Record<string, unknown>[]>([]);
const passedRecordOptions = ref<Record<string, unknown>[]>([]);

function fmtTime(v: unknown) {
  if (!v) return "";
  return String(v).replace("T", " ").slice(0, 19);
}

async function loadTpl() {
  const skip = (tplPage.value - 1) * tplLimit.value;
  try {
    const { data } = await listCertTemplates({
      skip,
      limit: tplLimit.value,
      keyword: tplKeyword.value.trim() || undefined,
    });
    tplTotal.value = data.total;
    tplRows.value = data.items || [];
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载模板失败"));
  }
}

async function loadRec() {
  const skip = (recPage.value - 1) * recLimit.value;
  try {
    const { data } = await listCertRecords({
      skip,
      limit: recLimit.value,
      keyword: recKeyword.value.trim() || undefined,
    });
    recTotal.value = data.total;
    recRows.value = data.items || [];
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载记录失败"));
  }
}

function searchTpl() {
  tplPage.value = 1;
  void loadTpl();
}

function searchRec() {
  recPage.value = 1;
  void loadRec();
}

function onTplPage(p: number) {
  tplPage.value = p;
  void loadTpl();
}

function onTplSize(sz: number) {
  tplLimit.value = sz;
  tplPage.value = 1;
  void loadTpl();
}

function onRecPage(p: number) {
  recPage.value = p;
  void loadRec();
}

function onRecSize(sz: number) {
  recLimit.value = sz;
  recPage.value = 1;
  void loadRec();
}

async function loadEnterprises() {
  if (!auth.isAdmin) return;
  try {
    const { data } = await listEnterprises({ skip: 0, limit: 500 });
    enterpriseOptions.value = (data.items || []).map((x: Record<string, unknown>) => ({
      id: x.id as number,
      name: (x.name as string) || "",
    }));
  } catch {
    enterpriseOptions.value = [];
  }
}

async function loadCoursesForTpl() {
  const eid = tplForm.value.enterprise_id;
  try {
    const { data } = await listCourses({
      skip: 0,
      limit: 500,
      enterprise_id: auth.isAdmin && eid ? eid : undefined,
    });
    courseOptions.value = (data.items || []).map((x: Record<string, unknown>) => ({
      id: x.id as number,
      name: (x.name as string) || "",
    }));
  } catch {
    courseOptions.value = [];
  }
}

function onTplEnterpriseChange() {
  tplForm.value.course_id = null;
  void loadCoursesForTpl();
}

async function openTplCreate() {
  tplEditId.value = null;
  tplForm.value = {
    enterprise_id: auth.isAdmin ? null : auth.me?.enterprise_id ?? null,
    cert_code: "",
    name: "",
    course_id: null,
    status: "draft",
    layout_json_str: "",
  };
  await loadEnterprises();
  await loadCoursesForTpl();
  tplDialog.value = true;
}

async function openTplEdit(row: Record<string, unknown>) {
  tplEditId.value = row.id as number;
  tplForm.value = {
    enterprise_id: (row.enterprise_id as number) || null,
    cert_code: String(row.cert_code || ""),
    name: String(row.name || ""),
    course_id: (row.course_id as number) || null,
    status: String(row.status || "draft"),
    layout_json_str: JSON.stringify(row.layout_json || {}, null, 2),
  };
  await loadEnterprises();
  await loadCoursesForTpl();
  tplDialog.value = true;
}

async function submitTpl() {
  if (auth.isAdmin && !tplEditId.value && !tplForm.value.enterprise_id) {
    ElMessage.warning("请选择所属企业");
    return;
  }
  if (!tplForm.value.cert_code.trim()) {
    ElMessage.warning("请填写模板编码");
    return;
  }
  let layout: Record<string, unknown> | undefined;
  const raw = tplForm.value.layout_json_str.trim();
  if (raw) {
    try {
      layout = JSON.parse(raw) as Record<string, unknown>;
    } catch {
      ElMessage.error("版式 JSON 格式不正确");
      return;
    }
  }
  try {
    if (tplEditId.value) {
      await patchCertTemplate(tplEditId.value, {
        name: tplForm.value.name,
        course_id: tplForm.value.course_id,
        status: tplForm.value.status,
        layout_json: layout,
      });
      ElMessage.success("已保存");
    } else {
      const body: Record<string, unknown> = {
        cert_code: tplForm.value.cert_code.trim(),
        name: tplForm.value.name,
        course_id: tplForm.value.course_id,
        status: tplForm.value.status,
      };
      if (auth.isAdmin && tplForm.value.enterprise_id) body.enterprise_id = tplForm.value.enterprise_id;
      if (layout) body.layout_json = layout;
      await createCertTemplate(body);
      ElMessage.success("已创建");
    }
    tplDialog.value = false;
    await loadTpl();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

async function onTplDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm("确定删除该证书模板？（无颁发记录时才可删除）", "提示", { type: "warning" });
  try {
    await deleteCertTemplate(row.id as number);
    ElMessage.success("已删除");
    await loadTpl();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "删除失败"));
  }
}

function openIssue() {
  issueForm.value = {
    cert_template_id: null,
    exam_service_record_id: null,
    require_passed: true,
  };
  issueDialog.value = true;
}

async function loadIssueOptions() {
  try {
    const [tplRes, recRes] = await Promise.all([
      listCertTemplates({ skip: 0, limit: 200 }),
      listExamServiceRecords({ skip: 0, limit: 200, passed: true }),
    ]);
    const items = (tplRes.data.items || []) as Record<string, unknown>[];
    issueTemplateOptions.value = items.filter((t) => t.status === "published");
    passedRecordOptions.value = (recRes.data.items || []) as Record<string, unknown>[];
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载选项失败"));
  }
}

function issueRecordLabel(r: Record<string, unknown>) {
  return `${r.exam_no} | ${r.student_display || "—"} | ${r.score}分 | ${r.course_name || ""}`;
}

async function submitIssue() {
  if (!issueForm.value.cert_template_id || !issueForm.value.exam_service_record_id) {
    ElMessage.warning("请选择模板与考试记录");
    return;
  }
  try {
    await issueCertRecord({
      cert_template_id: issueForm.value.cert_template_id,
      exam_service_record_id: issueForm.value.exam_service_record_id,
      require_passed: issueForm.value.require_passed,
    });
    ElMessage.success("颁发成功");
    issueDialog.value = false;
    activeTab.value = "rec";
    await loadRec();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "颁发失败"));
  }
}

watch(activeTab, (v) => {
  if (v === "tpl") void loadTpl();
  else void loadRec();
});

onMounted(() => {
  void loadTpl();
});
</script>

<style scoped>
.toolbar {
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}
.cert-tabs :deep(.el-tabs__content) {
  padding-top: 4px;
}
</style>
