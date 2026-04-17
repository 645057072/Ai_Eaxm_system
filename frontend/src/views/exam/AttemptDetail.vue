<template>
  <el-card v-loading="loading">
    <template #header>
      <div class="hdr">
        <span><AppEmoji name="list" size="sm" decorative />答卷 #{{ id }}</span>
        <el-button @click="$router.back()"><AppEmoji name="back" size="sm" decorative />返回</el-button>
      </div>
    </template>
    <template v-if="att">
      <p class="meta-line">状态：{{ attemptStatusLabel(att.status) }}，总分：{{ att.total_score ?? "-" }}</p>
      <div v-if="att.practice_report" class="report-wrap">
        <h3 class="report-title">练习报告</h3>
        <pre class="practice-report">{{ att.practice_report }}</pre>
        <p class="report-hint">（宋体五号样式展示，内容较长时可滚动查看或打印）</p>
      </div>
      <el-table :data="att.answers || []">
        <el-table-column prop="question_id" label="题目ID" width="90" />
        <el-table-column label="得分" width="90">
          <template #default="{ row }">{{ row.score_awarded ?? "-" }}</template>
        </el-table-column>
        <el-table-column label="作答" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ formatUserAnswer(row.user_answer_json) }}</template>
        </el-table-column>
      </el-table>
    </template>
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

function attemptStatusLabel(s: unknown): string {
  const key = String(s || "").trim();
  const m: Record<string, string> = {
    submitted: "已提交",
    in_progress: "作答中",
    timeout: "已超时",
  };
  return m[key] || key || "—";
}

/** 将作答 JSON 转为卷面可读中文/选项展示 */
function formatUserAnswer(val: unknown): string {
  if (val === true || val === "true") return "正确";
  if (val === false || val === "false") return "错误";
  if (val == null || val === "") return "—";
  if (Array.isArray(val)) {
    const arr = val
      .map((x) => String(x).trim().toUpperCase())
      .filter(Boolean);
    arr.sort();
    return arr.length ? arr.join("、") : "—";
  }
  if (typeof val === "object") {
    return JSON.stringify(val);
  }
  return String(val);
}

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
.meta-line {
  margin: 0 0 12px;
}
.report-wrap {
  margin-bottom: 16px;
}
.report-title {
  margin: 0 0 8px;
  font-size: 16px;
}
.practice-report {
  font-family: "SimSun", "Songti SC", "STSong", serif;
  font-size: 10.5pt;
  line-height: 1.45;
   max-height: none;
  overflow: visible;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  padding: 12px 14px;
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}
.report-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #64748b;
}
</style>
