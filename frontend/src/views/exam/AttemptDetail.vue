<template>
  <el-card v-loading="loading">
    <template #header>
      <div class="hdr">
        <span><AppEmoji name="list" size="sm" decorative />答卷 #{{ id }}</span>
        <el-button @click="$router.back()"><AppEmoji name="back" size="sm" decorative />返回</el-button>
      </div>
    </template>
    <p v-if="att">状态：{{ att.status }}，总分：{{ att.total_score ?? "-" }}</p>
    <el-table v-if="att" :data="att.answers || []">
      <el-table-column prop="question_id" label="题目ID" width="90" />
      <el-table-column label="得分" width="90">
        <template #default="{ row }">{{ row.score_awarded ?? "-" }}</template>
      </el-table-column>
      <el-table-column label="作答">
        <template #default="{ row }">{{ JSON.stringify(row.user_answer_json) }}</template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { getAttempt } from "@/api/attempts";

const route = useRoute();
const id = Number(route.params.id);
const loading = ref(false);
const att = ref<Record<string, unknown> | null>(null);

async function load() {
  loading.value = true;
  try {
    const { data } = await getAttempt(id);
    att.value = data as Record<string, unknown>;
  } catch {
    ElMessage.error("无权查看或记录不存在");
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
