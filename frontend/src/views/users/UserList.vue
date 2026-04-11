<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="用户名关键词" clearable style="width: 220px" />
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openCreate">新建用户</el-button>
    </div>
    <el-table :data="rows" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="full_name" label="姓名" />
      <el-table-column label="角色">
        <template #default="{ row }">{{ row.role?.name }}</template>
      </el-table-column>
      <el-table-column prop="is_active" label="启用" width="80">
        <template #default="{ row }">{{ row.is_active ? "是" : "否" }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
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

    <el-dialog v-model="dlg" :title="editId ? '编辑用户' : '新建用户'" width="480px">
      <el-form label-width="88px">
        <el-form-item v-if="!editId" label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="密码"
          ><el-input v-model="form.password" type="password" :placeholder="editId ? '不改请留空' : '必填'"
        /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.full_name" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_id" style="width: 100%">
            <el-option v-for="r in roleOpts" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editId" label="启用">
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
import { listUsers, createUser, patchUser, deleteUser } from "@/api/users";
import { listRoles } from "@/api/roles";

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
});

async function load() {
  const skip = (page.value - 1) * limit.value;
  const { data } = await listUsers({ skip, limit: limit.value, keyword: keyword.value || undefined });
  total.value = data.total;
  rows.value = data.items;
}

function openCreate() {
  editId.value = null;
  form.username = "";
  form.password = "";
  form.full_name = "";
  form.role_id = roleOpts.value[0]?.id ?? 1;
  form.is_active = true;
  dlg.value = true;
}

function openEdit(row: Record<string, unknown>) {
  editId.value = row.id as number;
  form.password = "";
  form.full_name = (row.full_name as string) || "";
  form.role_id = (row.role as { id: number }).id;
  form.is_active = !!row.is_active;
  dlg.value = true;
}

async function save() {
  try {
    if (!editId.value) {
      if (!form.username || !form.password) {
        ElMessage.warning("请填写用户名和密码");
        return;
      }
      await createUser({
        username: form.username,
        password: form.password,
        full_name: form.full_name || null,
        role_id: form.role_id,
      });
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
  } catch {
    ElMessage.error("保存失败");
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
</style>
