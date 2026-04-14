<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title"><AppEmoji name="sessions" size="sm" decorative />考试场次</div>
      </template>
      <div class="page-list-toolbar toolbar">
      <el-button type="success" @click="openCreate"><AppEmoji name="add" size="sm" decorative />新建场次</el-button>
    </div>
    <div class="page-list-body">
      <div class="page-list-table">
        <el-table :data="rows" height="100%">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="paper_id" label="试卷ID" width="90" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column label="开始" width="170">
        <template #default="{ row }">{{ fmt(row.start_at) }}</template>
      </el-table-column>
      <el-table-column label="结束" width="170">
        <template #default="{ row }">{{ fmt(row.end_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)"><AppEmoji name="edit" size="sm" decorative />编辑</el-button>
          <el-button v-if="row.status !== 'published'" link type="success" @click="publish(row)"
            ><AppEmoji name="publish" size="sm" decorative />发布</el-button
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

    <el-dialog v-model="dlg" :title="form.id ? '编辑场次' : '新建场次'" width="520px">
      <el-form label-width="100px">
        <el-form-item label="试卷ID"><el-input-number v-model="form.paper_id" :min="1" style="width: 100%" /></el-form-item>
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
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
import { ElMessage } from "element-plus";
import { listSessions, createSession, updateSession, publishSession } from "@/api/sessions";

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const dlg = ref(false);
const form = reactive({
  id: 0,
  paper_id: 1,
  title: "",
  start_at: "" as string | undefined,
  end_at: "" as string | undefined,
});

function fmt(v: unknown) {
  if (!v) return "";
  return String(v).replace("T", " ").slice(0, 19);
}

async function load() {
  const skip = (page.value - 1) * limit.value;
  const { data } = await listSessions({ skip, limit: limit.value });
  total.value = data.total;
  rows.value = data.items;
}

function openCreate() {
  form.id = 0;
  form.paper_id = 1;
  form.title = "";
  form.start_at = undefined;
  form.end_at = undefined;
  dlg.value = true;
}

function openEdit(row: Record<string, unknown>) {
  form.id = row.id as number;
  form.paper_id = row.paper_id as number;
  form.title = row.title as string;
  form.start_at = row.start_at as string | undefined;
  form.end_at = row.end_at as string | undefined;
  dlg.value = true;
}

async function save() {
  const body = {
    paper_id: form.paper_id,
    title: form.title,
    start_at: form.start_at || null,
    end_at: form.end_at || null,
  };
  try {
    if (!form.id) await createSession(body);
    else await updateSession(form.id, body);
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch {
    ElMessage.error("保存失败");
  }
}

async function publish(row: Record<string, unknown>) {
  await publishSession(row.id as number);
  ElMessage.success("已发布");
  await load();
}

onMounted(load);
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
