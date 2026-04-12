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
          <el-input v-model="form.code" placeholder="小写字母开头，如 auditor" />
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

    <el-drawer v-model="permVisible" title="功能授权" size="420px" destroy-on-close>
      <div v-if="permLoading" class="perm-loading">加载中...</div>
      <template v-else>
        <p class="perm-tip">按标签勾选本角色可使用的菜单、列表、表单字段与操作；未授权则无法访问对应功能与数据。</p>
        <div v-for="g in catalogGroups" :key="g.label" class="perm-group">
          <div class="perm-label">{{ g.label }}</div>
          <el-checkbox-group v-model="selectedList">
            <el-checkbox v-for="it in g.items" :key="it.code" :label="it.code" class="perm-item">
              {{ it.name }}（{{ it.kind }}）
            </el-checkbox>
          </el-checkbox-group>
        </div>
        <div class="perm-actions">
          <el-button type="primary" @click="savePerm">保存授权</el-button>
        </div>
      </template>
    </el-drawer>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { fetchPermissionCatalog } from "@/api/permissions";
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
const catalogGroups = ref<{ label: string; items: { code: string; name: string; kind: string }[] }[]>([]);
const selectedList = ref<string[]>([]);

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
    catalogGroups.value = cat.groups || [];
    selectedList.value = [...codes];
  } catch {
    ElMessage.error("加载授权数据失败");
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
  } catch {
    ElMessage.error("保存失败");
  }
}

watch(permVisible, (v) => {
  if (!v) {
    permRoleId.value = null;
    catalogGroups.value = [];
    selectedList.value = [];
  }
});

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
  } catch {
    ElMessage.error("保存失败");
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
</style>
