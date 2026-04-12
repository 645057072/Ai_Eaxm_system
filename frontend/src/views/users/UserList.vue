<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="用户名关键词" clearable style="width: 220px" />
      <el-button v-if="auth.can('list.user')" type="primary" @click="load"
        ><AppEmoji name="search" size="sm" decorative />查询</el-button
      >
      <el-button v-if="auth.can('action.user.create')" type="success" @click="openCreate"
        ><AppEmoji name="add" size="sm" decorative />新建用户</el-button
      >
    </div>
    <el-table :data="rows" style="width: 100%">
      <el-table-column v-if="auth.can('list.user')" prop="id" label="ID" width="80" />
      <el-table-column v-if="auth.can('field.user.username')" prop="username" label="用户名" />
      <el-table-column v-if="auth.can('field.user.full_name')" prop="full_name" label="姓名" />
      <el-table-column v-if="auth.can('field.user.enterprise')" label="所属企业" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ (row.enterprise as { name?: string } | null)?.name || "—" }}</template>
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
    <div class="pager">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="limit"
        @current-change="(p: number) => { page = p; load(); }"
      />
    </div>

    <el-dialog v-model="dlg" :title="editId ? '编辑用户' : '新建用户'" width="520px">
      <el-form label-width="100px">
        <el-form-item v-if="!editId && auth.can('field.user.username')" label="用户名"
          ><el-input v-model="form.username"
        /></el-form-item>
        <el-form-item v-if="!editId && auth.isAdmin && auth.can('field.user.enterprise')" label="所属企业" required>
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
        <el-form-item v-if="editId && auth.can('field.user.enterprise')" label="所属企业">
          <el-input :model-value="(editEnterpriseName as string) || '—'" disabled />
        </el-form-item>
        <el-form-item v-if="auth.can('field.user.role')" label="角色">
          <el-select v-model="form.role_id" style="width: 100%">
            <el-option v-for="r in roleOpts" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editId && auth.can('field.user.is_active')" label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { listEnterprises } from "@/api/enterprises";
import { listUsers, createUser, patchUser, deleteUser } from "@/api/users";
import { listRoles } from "@/api/roles";
import { useAuthStore } from "@/stores/auth";
import { systemEmojiRoleKey, type SystemEmojiKey } from "@/assets/emoji/systemEmoji";

const auth = useAuthStore();

function roleKey(row: Record<string, unknown>): SystemEmojiKey {
  const code = (row.role as { code?: string } | undefined)?.code;
  return systemEmojiRoleKey(code);
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
});
const enterpriseOpts = ref<{ id: number; name: string }[]>([]);
const editEnterpriseName = ref("");

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

function openCreate() {
  editId.value = null;
  editEnterpriseName.value = "";
  form.username = "";
  form.password = "";
  form.full_name = "";
  form.role_id = roleOpts.value[0]?.id ?? 1;
  form.is_active = true;
  form.enterprise_id = enterpriseOpts.value[0]?.id ?? auth.me?.enterprise?.id ?? null;
  dlg.value = true;
}

function openEdit(row: Record<string, unknown>) {
  editId.value = row.id as number;
  form.password = "";
  form.full_name = (row.full_name as string) || "";
  form.role_id = (row.role as { id: number }).id;
  form.is_active = !!row.is_active;
  editEnterpriseName.value = ((row.enterprise as { name?: string } | null)?.name as string) || "";
  dlg.value = true;
}

async function save() {
  try {
    if (!editId.value) {
      if (!form.username || !form.password) {
        ElMessage.warning("请填写用户名和密码");
        return;
      }
      if (auth.isAdmin && (form.enterprise_id == null || form.enterprise_id < 1)) {
        ElMessage.warning("请选择所属企业");
        return;
      }
      const body: Record<string, unknown> = {
        username: form.username,
        password: form.password,
        full_name: form.full_name || null,
        role_id: form.role_id,
      };
      if (auth.isAdmin) body.enterprise_id = form.enterprise_id;
      await createUser(body);
    } else {
      const body: Record<string, unknown> = {
        full_name: form.full_name || null,
        role_id: form.role_id,
        is_active: form.is_active,
      };
      if (form.password) body.password = form.password;
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
</style>
