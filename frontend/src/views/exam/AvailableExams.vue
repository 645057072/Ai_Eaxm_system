<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title"><AppEmoji name="availableExams" size="sm" decorative />可参加的考试</div>
      </template>
      <div class="page-list-body">
        <div class="page-list-table">
          <el-table :data="rows" v-loading="loading" height="100%">
      <el-table-column prop="id" label="场次ID" width="90" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="paper_id" label="试卷ID" width="90" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button type="primary" link @click="goTake(row.id)"
            ><AppEmoji name="enterExam" size="sm" decorative />进入考试</el-button
          >
        </template>
      </el-table-column>
    </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { listAvailable } from "@/api/sessions";

const router = useRouter();
const rows = ref<Record<string, unknown>[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const { data } = await listAvailable();
    rows.value = data.items;
  } catch {
    ElMessage.error("加载失败");
  } finally {
    loading.value = false;
  }
}

function goTake(sessionId: number) {
  router.push("/exam/take/" + sessionId);
}

onMounted(load);
</script>
