<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title"><AppEmoji name="paperLevel" size="sm" decorative />试卷等级</div>
      </template>
      <div class="page-list-toolbar toolbar">
      <el-input
        v-model="searchKeyword"
        clearable
        placeholder="等级编号 / 名称 / 职称系列"
        style="width: 260px"
        @keyup.enter="doSearch"
      />
      <el-button type="primary" @click="doSearch"><AppEmoji name="search" size="sm" decorative />查询</el-button>
      <el-button v-if="auth.can('action.paper_level.manage')" type="success" @click="router.push('/system/paper-level/new')"
        ><AppEmoji name="add" size="sm" decorative />新建等级</el-button
      >
    </div>
    <div class="page-list-body">
      <div class="page-list-table">
        <el-table :data="rows" height="100%" style="width: 100%">
      <template #empty>
        <el-empty description="暂无试卷等级" />
      </template>
      <el-table-column label="序号" width="72">
        <template #default="{ $index }">{{ (page - 1) * limit + $index + 1 }}</template>
      </el-table-column>
      <el-table-column prop="level_code" label="等级编号" width="120" show-overflow-tooltip />
      <el-table-column prop="level_name" label="等级名称" min-width="120" show-overflow-tooltip />
      <el-table-column prop="title_series" label="职称系列" min-width="120" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作员" width="110" show-overflow-tooltip>
        <template #default="{ row }">{{ (row.operator_name as string) || "—" }}</template>
      </el-table-column>
      <el-table-column label="所属企业" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ (row.enterprise_name as string) || "—" }}</template>
      </el-table-column>
      <el-table-column v-if="auth.can('action.paper_level.manage')" label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push('/system/paper-level/' + row.id + '/edit')"
            ><AppEmoji name="edit" size="sm" decorative />编辑</el-button
          >
          <el-button link type="danger" @click="onDelete(row)"><AppEmoji name="delete" size="sm" decorative />删除</el-button>
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
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { listPaperLevels, deletePaperLevel } from "@/api/paper_levels";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const searchKeyword = ref("");

function fmtTime(v: unknown) {
  if (!v) return "";
  return String(v).replace("T", " ").slice(0, 19);
}

async function load() {
  const skip = (page.value - 1) * limit.value;
  const params: Record<string, unknown> = { skip, limit: limit.value };
  const kw = searchKeyword.value.trim();
  if (kw) params.keyword = kw;
  const { data } = await listPaperLevels(params);
  total.value = data.total;
  rows.value = data.items;
}

function doSearch() {
  page.value = 1;
  load();
}

async function onDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm("确定删除该试卷等级？", "提示", { type: "warning" });
  try {
    await deletePaperLevel(row.id as number);
    ElMessage.success("已删除");
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "删除失败"));
  }
}

onMounted(load);
</script>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  align-items: center;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
