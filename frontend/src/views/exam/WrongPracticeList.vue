<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title">错题练习</div>
      </template>

      <div class="page-list-toolbar toolbar">
        <el-input
          v-model="keyword"
          clearable
          placeholder="课程名称"
          style="width: 220px"
          @keyup.enter="doSearch"
        />
        <el-button type="primary" @click="doSearch">查询</el-button>
      </div>

      <div class="page-list-body">
        <div class="page-list-table">
          <el-table :data="rows" height="100%" style="width: 100%">
            <template #empty>
              <el-empty description="暂无错题（交卷时错题/未答题将自动加入）" />
            </template>
            <el-table-column prop="course_name" label="课程名称" min-width="160" show-overflow-tooltip />
            <el-table-column prop="enterprise_name" label="所属企业" min-width="160" show-overflow-tooltip />
            <el-table-column prop="wrong_count" label="错题数" width="110" align="right" />
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  :disabled="Number(row.wrong_count || 0) <= 0"
                  @click="enter(row)"
                  ><AppEmoji name="enterExam" size="sm" decorative />进入练习</el-button
                >
              </template>
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
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { listWrongPracticeCourses } from "@/api/wrong_practice";

const router = useRouter();
const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(15);
const keyword = ref("");

async function load() {
  const skip = (page.value - 1) * limit.value;
  try {
    const { data } = await listWrongPracticeCourses({
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

function enter(row: Record<string, unknown>) {
  const cid = Number(row.course_id || 0);
  if (!cid) return;
  router.push(`/exam/wrong-practice/${cid}`);
}

onMounted(() => void load());
</script>

<style scoped>
.toolbar {
  flex-wrap: wrap;
  gap: 8px;
}
</style>

