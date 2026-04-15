<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title">考试服务</div>
      </template>
      <div class="page-list-toolbar toolbar">
        <el-input
          v-model="keyword"
          clearable
          placeholder="考试编号 / 课程 / 试卷 / 企业 / 学员"
          style="width: 320px"
          @keyup.enter="doSearch"
        />
        <el-button type="primary" @click="doSearch">查询</el-button>
      </div>
      <div class="page-list-body">
        <div class="page-list-table">
          <el-table :data="rows" height="100%" style="width: 100%">
            <template #empty>
              <el-empty description="暂无考试服务记录（考生交卷后自动生成）" />
            </template>
            <el-table-column prop="exam_no" label="考试编号" width="130" show-overflow-tooltip />
            <el-table-column prop="course_name" label="课程名称" min-width="140" show-overflow-tooltip />
            <el-table-column prop="paper_title" label="试卷名称" min-width="160" show-overflow-tooltip />
            <el-table-column prop="enterprise_name" label="所属企业" min-width="140" show-overflow-tooltip />
            <el-table-column prop="student_display" label="学员" min-width="140" show-overflow-tooltip />
            <el-table-column label="得分" width="100" align="right">
              <template #default="{ row }">{{ row.score }}</template>
            </el-table-column>
            <el-table-column label="是否通过考试" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="row.passed ? 'success' : 'danger'" size="small">{{ row.passed ? "通过" : "未通过" }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="记录时间" width="170">
              <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </div>
        <div class="page-list-pager">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next"
            :total="total"
            :page-size="limit"
            :current-page="page"
            :page-sizes="[15, 50, 100]"
            @current-change="onPage"
            @size-change="onSize"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { listExamServiceRecords } from "@/api/exam_service_records";

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(15);
const keyword = ref("");

function fmtTime(v: unknown) {
  if (!v) return "";
  return String(v).replace("T", " ").slice(0, 19);
}

async function load() {
  const skip = (page.value - 1) * limit.value;
  try {
    const { data } = await listExamServiceRecords({
      skip,
      limit: limit.value,
      keyword: keyword.value.trim() || undefined,
    });
    total.value = data.total;
    rows.value = data.items || [];
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载失败"));
  }
}

function doSearch() {
  page.value = 1;
  void load();
}

function onPage(p: number) {
  page.value = p;
  void load();
}

function onSize(sz: number) {
  limit.value = sz;
  page.value = 1;
  void load();
}

onMounted(() => void load());
</script>

<style scoped>
.toolbar {
  flex-wrap: wrap;
  gap: 8px;
}
</style>
