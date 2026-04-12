<template>
  <el-card v-loading="loading">
    <template #header>
      <div class="hdr">
        <span><AppEmoji name="papers" size="sm" decorative />试卷 #{{ id }} {{ paper?.title }}</span>
        <el-button @click="$router.back()"><AppEmoji name="back" size="sm" decorative />返回</el-button>
      </div>
    </template>
    <p>时长：{{ paper?.duration_minutes }} 分钟，总分：{{ paper?.total_score }}</p>
    <div class="toolbar">
      <el-input-number v-model="addQid" :min="1" placeholder="题目ID" />
      <el-input-number v-model="addScore" :min="0" :step="0.5" />
      <el-input-number v-model="addOrder" :min="0" />
      <el-button type="primary" @click="addItem"><AppEmoji name="addToPaper" size="sm" decorative />加入试卷</el-button>
    </div>
    <el-table :data="paper?.items || []">
      <el-table-column prop="sort_order" label="序" width="70" />
      <el-table-column prop="score" label="分值" width="90" />
      <el-table-column prop="question_id" label="题目ID" width="90" />
      <el-table-column label="题干" show-overflow-tooltip>
        <template #default="{ row }">{{ row.question?.stem }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button link type="danger" @click="remove(row)"><AppEmoji name="remove" size="sm" decorative />移除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { getPaper, addPaperItem, removePaperItem } from "@/api/papers";

const route = useRoute();
const id = Number(route.params.id);
const loading = ref(false);
const paper = ref<Record<string, unknown> | null>(null);
const addQid = ref(1);
const addScore = ref(1);
const addOrder = ref(0);

async function refresh() {
  loading.value = true;
  try {
    const { data } = await getPaper(id);
    paper.value = data as Record<string, unknown>;
  } finally {
    loading.value = false;
  }
}

async function addItem() {
  try {
    await addPaperItem(id, { question_id: addQid.value, sort_order: addOrder.value, score: addScore.value });
    ElMessage.success("已添加");
    await refresh();
  } catch {
    ElMessage.error("添加失败（题目是否存在、是否重复）");
  }
}

async function remove(row: Record<string, unknown>) {
  await removePaperItem(id, row.id as number);
  ElMessage.success("已移除");
  await refresh();
}

onMounted(refresh);
</script>

<style scoped>
.hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.toolbar {
  display: flex;
  gap: 8px;
  margin: 12px 0;
  flex-wrap: wrap;
}
</style>
