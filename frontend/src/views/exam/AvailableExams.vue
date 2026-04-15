<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title"><AppEmoji name="availableExams" size="sm" decorative />在线考试</div>
      </template>
      <div class="page-list-toolbar toolbar">
        <el-input
          v-model="kwPaperTitle"
          clearable
          placeholder="试卷标题"
          style="width: 180px"
          @keyup.enter="doSearch"
        />
        <el-input v-model="kwCourse" clearable placeholder="课程" style="width: 160px" @keyup.enter="doSearch" />
        <el-button type="primary" @click="doSearch"><AppEmoji name="search" size="sm" decorative />查询</el-button>
      </div>
      <div class="page-list-body">
        <div class="page-list-table">
          <el-table :data="rows" v-loading="loading" height="100%">
            <el-table-column prop="session_code" label="场次编号" width="120" show-overflow-tooltip />
            <el-table-column prop="title" label="标题" min-width="140" show-overflow-tooltip />
            <el-table-column label="课程" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">{{ (row.course_name as string) || "—" }}</template>
            </el-table-column>
            <el-table-column label="考试时长(分)" width="110" align="center">
              <template #default="{ row }">{{ formatDuration(row.paper_duration_minutes) }}</template>
            </el-table-column>
            <el-table-column label="试卷编号" width="130" show-overflow-tooltip>
              <template #default="{ row }">{{ (row.paper_no as string) || "—" }}</template>
            </el-table-column>
            <el-table-column label="试卷类型" width="110" align="center">
              <template #default="{ row }">{{ paperTypeLabel(row.paper_type as string | undefined) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button type="primary" link @click="goTake(row.id as number)"
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
import { onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { listAvailable } from "@/api/sessions";

const router = useRouter();
const rows = ref<Record<string, unknown>[]>([]);
const loading = ref(false);
const kwPaperTitle = ref("");
const kwCourse = ref("");

function paperTypeLabel(t?: string) {
  const v = (t || "").trim();
  if (!v) return "—";
  if (v === "practice") return "练习";
  if (v === "mock") return "模拟";
  if (v === "formal") return "正式";
  return v;
}

function formatDuration(v: unknown) {
  if (v == null || v === "") return "—";
  const n = Number(v);
  return Number.isFinite(n) ? String(n) : "—";
}

async function load() {
  loading.value = true;
  try {
    const params: Record<string, unknown> = { skip: 0, limit: 100 };
    const a = kwPaperTitle.value.trim();
    const b = kwCourse.value.trim();
    if (a) params.paper_title_keyword = a;
    if (b) params.course_keyword = b;
    const { data } = await listAvailable(params);
    rows.value = data.items;
  } catch {
    ElMessage.error("加载失败");
  } finally {
    loading.value = false;
  }
}

function doSearch() {
  void load();
}

function goTake(sessionId: number) {
  router.push("/exam/take/" + sessionId);
}

const suppressWatch = ref(true);
let debounce: ReturnType<typeof setTimeout> | null = null;
watch([kwPaperTitle, kwCourse], () => {
  if (suppressWatch.value) return;
  if (debounce) clearTimeout(debounce);
  debounce = setTimeout(() => {
    debounce = null;
    void load();
  }, 400);
});

onMounted(async () => {
  await load();
  suppressWatch.value = false;
});
</script>

<style scoped>
.toolbar {
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
</style>
