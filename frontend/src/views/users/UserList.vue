<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title"><AppEmoji name="userInfo" size="sm" decorative />用户信息</div>
      </template>
      <div class="page-list-toolbar toolbar">
      <el-input v-model="keyword" placeholder="用户名关键词" clearable style="width: 220px" />
      <el-button v-if="auth.can('list.user')" type="primary" @click="load"
        ><AppEmoji name="search" size="sm" decorative />查询</el-button
      >
      <el-button v-if="auth.can('action.user.import')" type="warning" @click="openImport"
        ><AppEmoji name="upload" size="sm" decorative />导入用户</el-button
      >
      <el-button v-if="auth.can('action.user.create')" type="success" @click="openCreate"
        ><AppEmoji name="add" size="sm" decorative />新建用户</el-button
      >
    </div>
    <div class="page-list-body">
      <div class="page-list-table">
        <el-table :data="rows" height="100%" style="width: 100%">
      <el-table-column v-if="auth.can('list.user')" prop="id" label="ID" width="80" />
      <el-table-column v-if="auth.can('field.user.username')" prop="username" label="用户名" />
      <el-table-column v-if="auth.can('field.user.full_name')" prop="full_name" label="姓名" />
      <el-table-column v-if="auth.can('field.user.student')" label="关联学员" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ rowStudentLabel(row) }}</template>
      </el-table-column>
      <el-table-column v-if="auth.can('field.user.enterprise')" label="所属企业" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ rowEnterpriseName(row) }}</template>
      </el-table-column>
      <el-table-column v-if="auth.can('field.user.role')" label="角色">
        <template #default="{ row }">
          <span class="cell-with-ico">
            <AppEmoji :name="roleKey(row)" size="sm" decorative />
            {{ row.role?.name }}
          </span>
        </template>
      </el-table-column>
      <el-table-column v-if="auth.can('field.user.is_active')" prop="is_active" label="启用" width="100">
        <template #default="{ row }">
          <span class="cell-with-ico">
            <AppEmoji :name="row.is_active ? 'enabledYes' : 'enabledNo'" size="sm" decorative />
            {{ row.is_active ? "是" : "否" }}
          </span>
        </template>
      </el-table-column>
      <el-table-column v-if="auth.can('field.user.enable_date')" label="启用日期" width="110" align="center">
        <template #default="{ row }">{{ fmtDate(row.enable_date) }}</template>
      </el-table-column>
      <el-table-column v-if="auth.can('field.user.expire_date')" label="失效日期" width="110" align="center">
        <template #default="{ row }">{{ fmtDate(row.expire_date) }}</template>
      </el-table-column>
      <el-table-column
        v-if="auth.canAny('action.user.update', 'action.user.delete')"
        label="操作"
        width="220"
      >
        <template #default="{ row }">
          <el-button v-if="auth.can('action.user.update')" link type="primary" @click="openEdit(row)"
            ><AppEmoji name="edit" size="sm" decorative />编辑</el-button
          >
          <el-button v-if="auth.can('action.user.delete')" link type="danger" @click="onDelete(row)"
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

    <el-dialog v-model="dlg" :title="editId ? '编辑用户' : '新建用户'" width="520px">
      <el-form label-width="100px">
        <el-form-item v-if="!editId && auth.can('field.user.username')" label="用户名"
          ><el-input v-model="form.username"
        /></el-form-item>
        <el-form-item
          v-if="!editId && canAssignSubsidiaryEnterprise && auth.can('field.user.enterprise')"
          label="所属企业"
          required
        >
          <el-select v-model="form.enterprise_id" placeholder="请选择企业" filterable style="width: 100%">
            <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!editId && auth.can('field.user.password')" label="密码" required>
          <el-input v-model="form.password" type="password" placeholder="必填" />
        </el-form-item>
        <template v-if="editId && auth.can('field.user.password') && (auth.isAdmin || auth.can('field.user.enterprise'))">
          <el-divider content-position="left">密码管理（重置）</el-divider>
          <el-form-item label="新密码">
            <el-input v-model="form.password" type="password" placeholder="填写则重置为该密码" />
          </el-form-item>
        </template>
        <el-form-item v-if="auth.can('field.user.full_name')" label="姓名"><el-input v-model="form.full_name" /></el-form-item>
        <el-form-item v-if="auth.can('field.user.student')" label="关联学员">
          <el-select
            v-model="form.student_id"
            clearable
            filterable
            remote
            :remote-method="remoteSearchStudent"
            :loading="studentLoading"
            placeholder="按学员编号/姓名搜索"
            style="width: 100%"
          >
            <el-option v-for="s in studentOpts" :key="s.id" :label="studentOptLabel(s)" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editId && auth.can('field.user.enterprise')" label="所属企业">
          <el-input :model-value="(editEnterpriseName as string) || '—'" disabled />
        </el-form-item>
        <el-form-item v-if="auth.can('field.user.role')" label="角色">
          <el-select v-model="form.role_id" style="width: 100%">
            <el-option v-for="r in roleOpts" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <template v-if="!editId && dlg">
          <el-form-item label="角色功能与数据">
            <p class="scope-tip">
              数据范围由「所属企业」与下列已授权功能共同决定；题库、试卷等通常仅本企业数据（超管除外）。
            </p>
            <div v-if="rolePreviewLoading" class="muted">加载角色权限...</div>
            <div v-else-if="!rolePreviewModules.length" class="muted">选择角色后将展示功能树（需具备用户维护或功能授权权限）</div>
            <div v-else class="preview-panel">
              <div v-for="mod in rolePreviewModules" :key="mod.moduleKey" class="pv-mod">
                <div v-if="modHasAny(mod)" class="pv-mod-inner">
                  <div class="pv-mod-title">{{ mod.moduleTitle }}</div>
                  <template v-if="pickedMenus(mod).length">
                    <div class="pv-kind">菜单</div>
                    <div v-for="m in pickedMenus(mod)" :key="m.code" class="pv-line d1">
                      <el-checkbox :model-value="true" disabled>{{ m.name }}</el-checkbox>
                    </div>
                  </template>
                  <template v-if="mod.lists.some((row) => pickedListOrFields(row).show)">
                    <div class="pv-kind">列表</div>
                    <template v-for="row in mod.lists" :key="row.item.code">
                      <div v-if="pickedListOrFields(row).show" class="pv-lf">
                        <div class="pv-line d1">
                          <el-checkbox :model-value="rolePreviewCodes.includes(row.item.code)" disabled>
                            {{ row.item.name }}
                          </el-checkbox>
                        </div>
                        <div v-for="f in pickedListOrFields(row).fields" :key="f.code" class="pv-line d2">
                          <el-checkbox :model-value="true" disabled>{{ f.name }}</el-checkbox>
                        </div>
                      </div>
                    </template>
                  </template>
                  <template v-if="mod.forms.some((row) => pickedListOrFields(row).show)">
                    <div class="pv-kind">表单</div>
                    <template v-for="row in mod.forms" :key="row.item.code">
                      <div v-if="pickedListOrFields(row).show" class="pv-lf">
                        <div class="pv-line d1">
                          <el-checkbox :model-value="rolePreviewCodes.includes(row.item.code)" disabled>
                            {{ row.item.name }}
                          </el-checkbox>
                        </div>
                        <div v-for="f in pickedListOrFields(row).fields" :key="f.code" class="pv-line d2">
                          <el-checkbox :model-value="true" disabled>{{ f.name }}</el-checkbox>
                        </div>
                      </div>
                    </template>
                  </template>
                  <template v-if="pickedActions(mod).length">
                    <div class="pv-kind">操作</div>
                    <div v-for="a in pickedActions(mod)" :key="a.code" class="pv-line d1">
                      <el-checkbox :model-value="true" disabled>{{ a.name }}</el-checkbox>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </el-form-item>
        </template>
        <el-form-item v-if="editId && auth.can('field.user.is_active')" label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item v-if="auth.can('field.user.enable_date')" label="启用日期">
          <el-date-picker v-model="form.enable_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item v-if="auth.can('field.user.expire_date')" label="失效日期">
          <el-date-picker v-model="form.expire_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDlg" title="导入用户" width="560px">
      <div class="muted" style="margin-bottom: 10px">
        支持 Word(docx)/Excel(xls,xlsx)/txt/csv。导入列：用户名、姓名、所属企业、角色、失效日期（启用日期默认当天，可选列：启用日期）。
      </div>
      <el-upload
        :auto-upload="false"
        :limit="1"
        :on-change="onImportFileChange"
        :show-file-list="true"
        accept=".docx,.xls,.xlsx,.csv,.txt"
      >
        <el-button type="primary"><AppEmoji name="upload" size="sm" decorative />选择文件</el-button>
      </el-upload>
      <template #footer>
        <el-button @click="importDlg = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { listEnterprises } from "@/api/enterprises";
import { listUsers, createUser, patchUser, deleteUser, importUsers } from "@/api/users";
import { listRoles, fetchRolePermissions } from "@/api/roles";
import { fetchPermissionCatalog, type AuthModulePayload, type CatalogItem } from "@/api/permissions";
import { useAuthStore } from "@/stores/auth";
import { systemEmojiRoleKey, type SystemEmojiKey } from "@/assets/emoji/systemEmoji";
import { lookupStudents } from "@/api/students";

const auth = useAuthStore();

/** 全局管理员或企业侧「XX管理员」可为新建用户指定本企业或下级企业 */
const canAssignSubsidiaryEnterprise = computed(() => {
  if (auth.isAdmin) return true;
  const n = (auth.me?.role?.name || "").trim();
  return n.endsWith("管理员");
});

function roleKey(row: Record<string, unknown>): SystemEmojiKey {
  const code = (row.role as { code?: string } | undefined)?.code;
  return systemEmojiRoleKey(code);
}

/** 列表行所属企业名称（模板中不用 TS 断言，避免 vue-tsc 报错） */
function rowEnterpriseName(row: Record<string, unknown>) {
  const e = row.enterprise as { name?: string } | null | undefined;
  return e?.name || "—";
}

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const keyword = ref("");

const dlg = ref(false);
const editId = ref<number | null>(null);
const roleOpts = ref<{ id: number; name: string }[]>([]);
const form = reactive({
  username: "",
  password: "",
  full_name: "",
  role_id: 1,
  is_active: true,
  enterprise_id: null as number | null,
  student_id: null as number | null,
  enable_date: "" as string | "",
  expire_date: "" as string | "",
});
const enterpriseOpts = ref<{ id: number; name: string }[]>([]);
const editEnterpriseName = ref("");
/** 编辑用户时该行所属企业 ID，用于关联学员仅检索本企业学员 */
const editEnterpriseId = ref<number | null>(null);

function fmtDate(v: unknown) {
  if (!v) return "—";
  return String(v);
}

function rowStudentLabel(row: Record<string, unknown>) {
  const s = row.student as { student_no?: string; full_name?: string } | null | undefined;
  if (!s) return "—";
  const name = (s.full_name || "").trim();
  const no = (s.student_no || "").trim();
  if (name && no) return `${name}（${no}）`;
  return name || no || "—";
}

const studentOpts = ref<{ id: number; student_no: string; full_name: string }[]>([]);
const studentLoading = ref(false);
function studentOptLabel(s: { student_no: string; full_name: string }) {
  const name = (s.full_name || "").trim();
  const no = (s.student_no || "").trim();
  if (name && no) return `${name}（${no}）`;
  return name || no || "—";
}

function scopeEnterpriseIdForStudent(): number | null {
  if (editId.value) return editEnterpriseId.value;
  return form.enterprise_id ?? auth.me?.enterprise?.id ?? null;
}

let studentFetchTimer: any = null;
async function remoteSearchStudent(q: string) {
  if (studentFetchTimer) clearTimeout(studentFetchTimer);
  studentFetchTimer = setTimeout(async () => {
    const kw = (q || "").trim();
    const entId = scopeEnterpriseIdForStudent();
    if (!kw) {
      return;
    }
    if (entId == null) {
      studentOpts.value = [];
      ElMessage.warning("请先选择所属企业后再检索学员");
      return;
    }
    studentLoading.value = true;
    try {
      const params: Record<string, unknown> = { keyword: kw, limit: 20, enterprise_id: entId };
      const res = await lookupStudents(params);
      const items = (res.data?.items || []) as any[];
      studentOpts.value = items.map((x) => ({ id: x.id, student_no: x.student_no, full_name: x.full_name }));
    } finally {
      studentLoading.value = false;
    }
  }, 250);
}

function todayStr() {
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

const importDlg = ref(false);
const importing = ref(false);
let importFile: File | null = null;
function openImport() {
  importFile = null;
  importDlg.value = true;
}
function onImportFileChange(file: any) {
  importFile = file?.raw || null;
}
async function doImport() {
  if (!importFile) {
    ElMessage.warning("请选择导入文件");
    return;
  }
  importing.value = true;
  try {
    const fd = new FormData();
    fd.append("file", importFile);
    const res = await importUsers(fd);
    const created = res.data?.created ?? 0;
    const skipped = res.data?.skipped ?? 0;
    ElMessage.success(`导入完成：新增 ${created}，跳过 ${skipped}`);
    importDlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "导入失败"));
  } finally {
    importing.value = false;
  }
}

const rolePreviewLoading = ref(false);
const rolePreviewCodes = ref<string[]>([]);
const rolePreviewModules = ref<AuthModulePayload[]>([]);

function pickedMenus(mod: AuthModulePayload) {
  return mod.menus.filter((m) => rolePreviewCodes.value.includes(m.code));
}

function pickedActions(mod: AuthModulePayload) {
  return mod.actions.filter((a) => rolePreviewCodes.value.includes(a.code));
}

function pickedListOrFields(row: { item: CatalogItem; fields: CatalogItem[] }) {
  const hasList = rolePreviewCodes.value.includes(row.item.code);
  const fields = row.fields.filter((f) => rolePreviewCodes.value.includes(f.code));
  return { show: hasList || fields.length > 0, fields };
}

function modHasAny(mod: AuthModulePayload) {
  if (pickedMenus(mod).length) return true;
  if (pickedActions(mod).length) return true;
  if (mod.lists.some((row) => pickedListOrFields(row).show)) return true;
  if (mod.forms.some((row) => pickedListOrFields(row).show)) return true;
  return false;
}

watch(
  () => form.enterprise_id,
  () => {
    if (!editId.value) {
      form.student_id = null;
      studentOpts.value = [];
    }
  },
);

watch(
  [() => dlg.value, () => form.role_id, () => editId.value],
  async ([d, rid, eid]) => {
    if (!d || eid) {
      rolePreviewCodes.value = [];
      rolePreviewModules.value = [];
      return;
    }
    if (!rid) {
      rolePreviewCodes.value = [];
      rolePreviewModules.value = [];
      return;
    }
    rolePreviewLoading.value = true;
    try {
      const [{ data: codes }, { data: cat }] = await Promise.all([
        fetchRolePermissions(rid as number),
        fetchPermissionCatalog(),
      ]);
      rolePreviewCodes.value = codes;
      rolePreviewModules.value = cat.authModules || [];
    } catch {
      rolePreviewCodes.value = [];
      rolePreviewModules.value = [];
    } finally {
      rolePreviewLoading.value = false;
    }
  },
);

async function load() {
  try {
    const skip = (page.value - 1) * limit.value;
    const { data } = await listUsers({ skip, limit: limit.value, keyword: keyword.value || undefined });
    total.value = data.total;
    rows.value = data.items;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载失败"));
  }
}

async function openCreate() {
  editId.value = null;
  editEnterpriseName.value = "";
  editEnterpriseId.value = null;
  form.username = "";
  form.password = "";
  form.full_name = "";
  form.role_id = roleOpts.value[0]?.id ?? 1;
  form.is_active = true;
  form.enterprise_id = auth.me?.enterprise?.id ?? enterpriseOpts.value[0]?.id ?? null;
  form.student_id = null;
  form.enable_date = todayStr();
  form.expire_date = "";
  studentOpts.value = [];
  if (canAssignSubsidiaryEnterprise.value) {
    try {
      const { data } = await listEnterprises({ skip: 0, limit: 500 });
      enterpriseOpts.value = (data.items || []).map((x: { id: number; name: string }) => ({ id: x.id, name: x.name }));
      if (!auth.isAdmin && auth.me?.enterprise?.id) {
        form.enterprise_id = auth.me.enterprise.id;
      } else if (!form.enterprise_id && enterpriseOpts.value.length) {
        form.enterprise_id = enterpriseOpts.value[0].id;
      }
    } catch {
      /* 忽略，保存时再提示 */
    }
  }
  dlg.value = true;
}

function openEdit(row: Record<string, unknown>) {
  editId.value = row.id as number;
  form.password = "";
  form.full_name = (row.full_name as string) || "";
  form.role_id = (row.role as { id: number }).id;
  form.is_active = !!row.is_active;
  editEnterpriseName.value = ((row.enterprise as { name?: string } | null)?.name as string) || "";
  editEnterpriseId.value =
    (row.enterprise_id as number | null | undefined) ??
    ((row.enterprise as { id?: number } | null | undefined)?.id as number | undefined) ??
    null;
  form.student_id = (row.student_id as number) || null;
  form.enable_date = (row.enable_date as string) || "";
  form.expire_date = (row.expire_date as string) || "";
  const st = row.student as { id: number; student_no?: string; full_name?: string } | null | undefined;
  if (st && form.student_id) {
    studentOpts.value = [
      {
        id: st.id,
        student_no: (st.student_no || "") as string,
        full_name: (st.full_name || "") as string,
      },
    ];
  } else {
    studentOpts.value = [];
  }
  dlg.value = true;
}

async function save() {
  try {
    if (!editId.value) {
      const username = (form.username || "").trim();
      const password = form.password || "";
      if (!username || !password) {
        ElMessage.warning("请填写用户名和密码");
        return;
      }
      if (username.length < 2) {
        ElMessage.warning("用户名至少 2 个字符");
        return;
      }
      if (password.length < 6) {
        ElMessage.warning("密码至少 6 位");
        return;
      }
      const fn = (form.full_name || "").trim();
      if (fn.length > 64) {
        ElMessage.warning("姓名最长 64 个字符");
        return;
      }
      const roleIdNum = Number(form.role_id);
      if (!Number.isFinite(roleIdNum) || roleIdNum < 1) {
        ElMessage.warning("请选择有效角色");
        return;
      }
      let enterpriseIdNum: number | undefined;
      if (canAssignSubsidiaryEnterprise.value) {
        const raw = form.enterprise_id;
        const n = raw == null ? NaN : Number(raw);
        if (!Number.isFinite(n) || n < 1) {
          ElMessage.warning("请选择所属企业");
          return;
        }
        enterpriseIdNum = n;
      }
      const body: Record<string, unknown> = {
        username,
        password,
        full_name: fn || null,
        role_id: roleIdNum,
        student_id: form.student_id || null,
        enable_date: form.enable_date || null,
        expire_date: form.expire_date || null,
      };
      if (canAssignSubsidiaryEnterprise.value && enterpriseIdNum != null) body.enterprise_id = enterpriseIdNum;
      await createUser(body);
    } else {
      const fn = (form.full_name || "").trim();
      if (fn.length > 64) {
        ElMessage.warning("姓名最长 64 个字符");
        return;
      }
      const roleIdNum = Number(form.role_id);
      if (!Number.isFinite(roleIdNum) || roleIdNum < 1) {
        ElMessage.warning("请选择有效角色");
        return;
      }
      const body: Record<string, unknown> = {
        full_name: fn || null,
        role_id: roleIdNum,
        is_active: form.is_active,
        student_id: form.student_id || null,
        enable_date: form.enable_date || null,
        expire_date: form.expire_date || null,
      };
      if (form.password) {
        if (form.password.length < 6) {
          ElMessage.warning("新密码至少 6 位");
          return;
        }
        body.password = form.password;
      }
      await patchUser(editId.value, body);
    }
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

async function onDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm("确定删除该用户？", "提示", { type: "warning" });
  await deleteUser(row.id as number);
  ElMessage.success("已删除");
  await load();
}

onMounted(async () => {
  const { data } = await listRoles();
  roleOpts.value = data;
  if (auth.isAdmin) {
    try {
      const { data: ent } = await listEnterprises({ skip: 0, limit: 200 });
      enterpriseOpts.value = ent.items.map((x: { id: number; name: string }) => ({ id: x.id, name: x.name }));
    } catch {
      enterpriseOpts.value = [];
    }
  }
  await load();
});
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.cell-with-ico {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.scope-tip {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  margin: 0 0 8px;
}
.muted {
  font-size: 13px;
  color: #94a3b8;
}
.preview-panel {
  max-height: 240px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fafbfc;
}
.pv-mod-inner {
  margin-bottom: 12px;
}
.pv-mod-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
  font-size: 13px;
}
.pv-kind {
  font-size: 11px;
  color: #94a3b8;
  margin: 6px 0 2px;
}
.pv-line {
  padding: 2px 0;
}
.pv-line.d1 {
  padding-left: 4px;
}
.pv-line.d2 {
  padding-left: 24px;
  border-left: 2px solid #e2e8f0;
  margin-left: 8px;
}
.pv-lf {
  margin-bottom: 6px;
}
</style>
