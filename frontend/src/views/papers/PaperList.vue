<template>
  <el-card>
    <div class="toolbar">
      <el-button type="success" @click="openCreate">新建试卷</el-button>
    </div>
    <el-table :data="rows">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="duration_minutes" label="时长(分)" width="100" />
      <el-table-column prop="total_score" label="总分" width="90" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push('/papers/' + row.id)">组卷</el-button>
          <el-button link type="danger" @click="onDel(row)">删除</el-button>
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

    <el-dialog v-model="dlg" title="新建试卷" width="480px">
      <el-form label-width="100px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="时长(分)"><el-input-number v-model="form.duration_minutes" :min="1" :max="600" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="saveCreate">创建</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { listPapers, createPaper, deletePaper } from "@/api/papers";

const router = useRouter();
const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const dlg = ref(false);
const form = reactive({ title: "", description: "", duration_minutes: 60 });

async function load() {
  const skip = (page.value - 1) * limit.value;
  const { data } = await listPapers({ skip, limit: limit.value });
  total.value = data.total;
  rows.value = data.items;
}

function openCreate() {
  form.title = "";
  form.description = "";
  form.duration_minutes = 60;
  dlg.value = true;
}

async function saveCreate() {
  const { data } = await createPaper({
    title: form.title,
    description: form.description || null,
    duration_minutes: form.duration_minutes,
  });
  ElMessage.success("已创建");
  dlg.value = false;
  await router.push("/papers/" + data.id);
}

async function onDel(row: Record<string, unknown>) {
  await ElMessageBox.confirm("确定删除该试卷？", "提示", { type: "warning" });
  await deletePaper(row.id as number);
  ElMessage.success("已删除");
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
