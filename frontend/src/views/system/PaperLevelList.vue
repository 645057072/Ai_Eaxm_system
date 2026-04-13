<template>
  <el-card>
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        clearable
        placeholder="等级编号 / 名称 / 职称系列"
        style="width: 260px"
        @keyup.enter="doSearch"
      />
      <el-button type="primary" @click="doSearch"><AppEmoji name="search" size="sm" decorative />查询</el-button>
      <el-button v-if="auth.can('action.paper_level.manage')" type="success" @click="openCreate"
        ><AppEmoji name="add" size="sm" decorative />新建等级</el-button
      >
    </div>
    <el-table :data="rows" style="width: 100%">
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
          <el-button link type="primary" @click="openEdit(row)"><AppEmoji name="edit" size="sm" decorative />编辑</el-button>
          <el-button link type="danger" @click="onDelete(row)"><AppEmoji name="delete" size="sm" decorative />删除</el-button>
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

    <el-dialog v-model="dlg" :title="editId ? '编辑试卷等级' : '新建试卷等级'" width="520px">
      <el-form label-width="100px">
        <el-form-item v-if="!editId && auth.isAdmin" label="所属企业" required>
          <el-select v-model="form.enterprise_id" placeholder="请选择企业" filterable style="width: 100%">
            <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editId" label="所属企业">
          <el-input :model-value="editEnterpriseName" disabled />
        </el-form-item>
        <el-form-item label="等级编号" required>
          <el-input v-model="form.level_code" placeholder="等级编号" />
        </el-form-item>
        <el-form-item label="等级名称" required>
          <el-input v-model="form.level_name" placeholder="等级名称" />
        </el-form-item>
        <el-form-item label="职称系列" required>
          <el-input v-model="form.title_series" placeholder="职称系列" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { listEnterprises } from "@/api/enterprises";
import { listPaperLevels, createPaperLevel, patchPaperLevel, deletePaperLevel } from "@/api/paper_levels";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const searchKeyword = ref("");
const dlg = ref(false);
const editId = ref<number | null>(null);
const enterpriseOpts = ref<{ id: number; name: string }[]>([]);
const editEnterpriseName = ref("");

const form = reactive({
  enterprise_id: undefined as number | undefined,
  level_code: "",
  level_name: "",
  title_series: "",
});

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

async function openCreate() {
  editId.value = null;
  form.level_code = "";
  form.level_name = "";
  form.title_series = "";
  form.enterprise_id = enterpriseOpts.value[0]?.id;
  dlg.value = true;
}

function openEdit(row: Record<string, unknown>) {
  editId.value = row.id as number;
  form.level_code = row.level_code as string;
  form.level_name = row.level_name as string;
  form.title_series = row.title_series as string;
  editEnterpriseName.value = (row.enterprise_name as string) || "";
  dlg.value = true;
}

async function save() {
  try {
    if (!editId.value) {
      const body: Record<string, unknown> = {
        level_code: form.level_code,
        level_name: form.level_name,
        title_series: form.title_series,
      };
      if (auth.isAdmin) {
        if (!form.enterprise_id) {
          ElMessage.warning("请选择所属企业");
          return;
        }
        body.enterprise_id = form.enterprise_id;
      }
      await createPaperLevel(body);
    } else {
      await patchPaperLevel(editId.value, {
        level_code: form.level_code,
        level_name: form.level_name,
        title_series: form.title_series,
      });
    }
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
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

onMounted(async () => {
  if (auth.isAdmin) {
    const { data } = await listEnterprises({ skip: 0, limit: 500 });
    enterpriseOpts.value = (data.items || []) as { id: number; name: string }[];
  }
  await load();
});
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
