<template>
  <el-card>
    <div class="toolbar">
      <el-button v-if="auth.can('action.role.create')" type="success" @click="openCreate"
        ><AppEmoji name="add" size="sm" decorative />新建角色</el-button
      >
    </div>
    <el-table :data="rows" style="width: 100%">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="角色名称" min-width="120" />
      <el-table-column prop="code" label="角色编码" width="140" />
      <el-table-column prop="description" label="说明" min-width="160" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button v-if="auth.can('action.role.permission')" link type="success" @click="openPerm(row)">
            功能授权
          </el-button>
          <el-button v-if="auth.can('action.role.update')" link type="primary" @click="openEdit(row)"
            ><AppEmoji name="edit" size="sm" decorative />编辑</el-button
          >
          <el-button
            v-if="auth.can('action.role.delete')"
            link
            type="danger"
            :disabled="isReserved(row.code as string)"
            @click="onDelete(row)"
          >
            <AppEmoji name="delete" size="sm" decorative />删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" :title="isCreate ? '新建角色' : '编辑角色'" width="480px">
      <el-form label-width="100px">
        <el-form-item v-if="isCreate" label="角色编码" required>
          <el-input v-model="form.code" placeholder="字母开头，保存时自动转小写，如 auditor" />
        </el-form-item>
        <el-form-item v-else label="角色编码">
          <el-input :model-value="form.code" disabled />
        </el-form-item>
        <el-form-item label="角色名称" required>
          <el-input v-model="form.name" placeholder="角色名称" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="permVisible"
      title="功能授权"
      width="820px"
      top="5vh"
      destroy-on-close
      class="perm-dialog"
      @closed="onPermDialogClosed"
    >
      <div v-if="permLoading" class="perm-loading">加载中...</div>
      <template v-else>
        <p class="perm-tip">
          按「功能模块」分组：同一模块内菜单、列表、表单为树形结构；列表/表单下附带其字段（横向标签）授权；底部为操作权限。新业务请在服务端 CATALOG 登记功能点。
        </p>
        <div class="perm-tree-wrap">
          <div v-for="mod in authModules" :key="mod.moduleKey" class="perm-fm-mod">
            <div class="perm-mod-title">{{ mod.moduleTitle }}</div>
            <div v-if="mod.menus.length" class="perm-row">
              <span class="perm-kind">菜单</span>
              <el-checkbox-group v-model="selectedList" class="perm-inline-group">
                <el-checkbox v-for="m in mod.menus" :key="m.code" :value="m.code">{{ m.name }}</el-checkbox>
              </el-checkbox-group>
            </div>
            <div v-for="row in mod.lists" :key="'l-' + row.item.code" class="perm-lf-card">
              <div class="perm-lf-head">
                <span class="perm-kind">列表</span>
                <el-checkbox
                  :model-value="selectedList.includes(row.item.code)"
                  @change="(v: boolean | string | number) => toggleCode(row.item.code, !!v)"
                >
                  {{ row.item.name }}
                </el-checkbox>
              </div>
              <div v-if="row.fields.length" class="perm-lf-fields">
                <span class="perm-field-hint">字段</span>
                <div class="field-tags">
                  <el-check-tag
                    v-for="it in row.fields"
                    :key="it.code"
                    :checked="selectedList.includes(it.code)"
                    class="field-tag"
                    @change="(on: boolean) => toggleCode(it.code, on)"
                  >
                    {{ it.name }}
                  </el-check-tag>
                </div>
              </div>
            </div>
            <div v-for="row in mod.forms" :key="'f-' + row.item.code" class="perm-lf-card">
              <div class="perm-lf-head">
                <span class="perm-kind">表单</span>
                <el-checkbox
                  :model-value="selectedList.includes(row.item.code)"
                  @change="(v: boolean | string | number) => toggleCode(row.item.code, !!v)"
                >
                  {{ row.item.name }}
                </el-checkbox>
              </div>
              <div v-if="row.fields.length" class="perm-lf-fields">
                <span class="perm-field-hint">字段</span>
                <div class="field-tags">
                  <el-check-tag
                    v-for="it in row.fields"
                    :key="it.code"
                    :checked="selectedList.includes(it.code)"
                    class="field-tag"
                    @change="(on: boolean) => toggleCode(it.code, on)"
                  >
                    {{ it.name }}
                  </el-check-tag>
                </div>
              </div>
            </div>
            <div v-if="mod.actions.length" class="perm-act-block">
              <span class="perm-kind">操作</span>
              <el-checkbox-group v-model="selectedList" class="perm-inline-group">
                <el-checkbox v-for="it in mod.actions" :key="it.code" :value="it.code">{{ it.name }}</el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
        </div>
        <div class="perm-actions">
          <el-button type="primary" @click="savePerm">保存授权</el-button>
        </div>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { fetchPermissionCatalog, type AuthModulePayload, type CatalogItem } from "@/api/permissions";
import { listRoles, createRole, patchRole, deleteRole, fetchRolePermissions, saveRolePermissions } from "@/api/roles";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const RESERVED = new Set(["admin", "teacher", "student"]);

const rows = ref<Record<string, unknown>[]>([]);
const dlg = ref(false);
const isCreate = ref(true);
const editId = ref<number | null>(null);

const form = reactive({
  code: "",
  name: "",
  description: "",
});

const permVisible = ref(false);
const permLoading = ref(false);
const permRoleId = ref<number | null>(null);
const authModules = ref<AuthModulePayload[]>([]);
const selectedList = ref<string[]>([]);

function toggleCode(code: string, on: boolean) {
  if (on) {
    if (!selectedList.value.includes(code)) selectedList.value.push(code);
  } else {
    selectedList.value = selectedList.value.filter((c) => c !== code);
  }
}

function isReserved(code: string) {
  return RESERVED.has(code);
}

function fmtTime(v: unknown) {
  if (!v) return "";
  return String(v).replace("T", " ").slice(0, 19);
}

async function load() {
  const { data } = await listRoles();
  rows.value = data;
}

function openCreate() {
  isCreate.value = true;
  editId.value = null;
  form.code = "";
  form.name = "";
  form.description = "";
  dlg.value = true;
}

function openEdit(row: Record<string, unknown>) {
  isCreate.value = false;
  editId.value = row.id as number;
  form.code = (row.code as string) || "";
  form.name = (row.name as string) || "";
  form.description = (row.description as string) || "";
  dlg.value = true;
}

async function openPerm(row: Record<string, unknown>) {
  permRoleId.value = row.id as number;
  permLoading.value = true;
  permVisible.value = true;
  selectedList.value = [];
  try {
    const [{ data: cat }, { data: codes }] = await Promise.all([
      fetchPermissionCatalog(),
      fetchRolePermissions(row.id as number),
    ]);
    authModules.value = cat.authModules?.length ? cat.authModules : [];
    selectedList.value = [...codes];
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载授权数据失败"));
    permVisible.value = false;
  } finally {
    permLoading.value = false;
  }
}

async function savePerm() {
  if (permRoleId.value == null) return;
  try {
    await saveRolePermissions(permRoleId.value, selectedList.value);
    ElMessage.success("已保存功能授权");
    permVisible.value = false;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

function onPermDialogClosed() {
  permRoleId.value = null;
  authModules.value = [];
  selectedList.value = [];
}

async function save() {
  if (!form.name.trim()) {
    ElMessage.warning("请填写角色名称");
    return;
  }
  try {
    if (isCreate.value) {
      if (!form.code.trim()) {
        ElMessage.warning("请填写角色编码");
        return;
      }
      await createRole({
        code: form.code.trim(),
        name: form.name.trim(),
        description: form.description.trim() || null,
      });
    } else if (editId.value != null) {
      await patchRole(editId.value, {
        name: form.name.trim(),
        description: form.description.trim() || null,
      });
    }
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

async function onDelete(row: Record<string, unknown>) {
  if (isReserved(row.code as string)) return;
  await ElMessageBox.confirm("确定删除该角色？若有用户绑定将无法删除。", "提示", { type: "warning" });
  await deleteRole(row.id as number);
  ElMessage.success("已删除");
  await load();
}

onMounted(load);
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
}
.perm-tip {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  margin: 0 0 16px;
}
.perm-group {
  margin-bottom: 16px;
}
.perm-label {
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
}
.perm-item {
  display: block;
  margin-left: 0;
  margin-bottom: 6px;
}
.perm-actions {
  margin-top: 20px;
}
.perm-loading {
  padding: 24px;
  text-align: center;
  color: #64748b;
}
.perm-dialog :deep(.el-dialog__body) {
  padding-top: 8px;
  max-height: calc(100vh - 160px);
  overflow-y: auto;
}
.perm-collapse {
  border: none;
}
.perm-tree-wrap {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  background: #fafbfc;
  max-height: 42vh;
  overflow-y: auto;
}
.perm-mod {
  margin-bottom: 14px;
}
.perm-mod:last-child {
  margin-bottom: 0;
}
.perm-mod-title {
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px dashed #cbd5e1;
}
.perm-group-block {
  margin-left: 8px;
  margin-bottom: 12px;
  padding-left: 10px;
  border-left: 2px solid #e2e8f0;
}
.perm-sub-title {
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
  font-size: 13px;
}
.perm-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-bottom: 8px;
}
.perm-kind {
  flex: 0 0 40px;
  font-size: 12px;
  color: #64748b;
  padding-top: 4px;
}
.perm-inline-group {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
}
.perm-fields-block,
.perm-actions-block {
  margin-top: 16px;
}
.perm-section-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 10px;
}
.perm-field-row {
  margin-bottom: 12px;
}
.perm-field-label {
  font-size: 13px;
  color: #475569;
  margin-bottom: 6px;
}
.field-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.field-tag {
  margin: 0;
}
.perm-fm-mod {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8ecf0;
}
.perm-fm-mod:last-child {
  border-bottom: none;
}
.perm-lf-card {
  margin: 10px 0 10px 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
}
.perm-lf-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.perm-lf-fields {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 8px;
  padding-left: 50px;
}
.perm-field-hint {
  flex: 0 0 auto;
  font-size: 12px;
  color: #94a3b8;
  padding-top: 4px;
}
.perm-act-block {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-top: 8px;
  flex-wrap: wrap;
}
</style>
