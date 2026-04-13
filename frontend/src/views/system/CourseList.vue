<template>
  <el-card>
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        clearable
        placeholder="课程名称 / 讲师 / 所属企业"
        style="width: 260px"
        @keyup.enter="doSearch"
      />
      <el-button type="primary" @click="doSearch"><AppEmoji name="search" size="sm" decorative />查询</el-button>
      <el-button v-if="auth.can('action.course.create')" type="success" @click="openCreate"
        ><AppEmoji name="add" size="sm" decorative />新建课程</el-button
      >
    </div>
    <el-table :data="rows" style="width: 100%">
      <template #empty>
        <el-empty description="暂无课程数据" />
      </template>
      <el-table-column label="序号" width="72">
        <template #default="{ $index }">{{ (page - 1) * limit + $index + 1 }}</template>
      </el-table-column>
      <el-table-column v-if="auth.can('field.course.name')" prop="name" label="课程名称" min-width="140" show-overflow-tooltip />
      <el-table-column v-if="auth.can('field.course.instructor')" prop="instructor" label="讲师" width="100" />
      <el-table-column v-if="auth.can('field.course.period')" prop="period_text" label="课程期间" width="160" show-overflow-tooltip />
      <el-table-column v-if="auth.can('field.course.description')" prop="description" label="课程简介" min-width="160" show-overflow-tooltip />
      <el-table-column v-if="auth.can('field.course.enterprise')" label="所属企业" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ (row.enterprise as { name?: string })?.name || "—" }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column
        v-if="auth.canAny('action.course.update', 'action.course.delete')"
        label="操作"
        width="180"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button v-if="auth.can('action.course.update')" link type="primary" @click="openEdit(row)"
            ><AppEmoji name="edit" size="sm" decorative />编辑</el-button
          >
          <el-button v-if="auth.can('action.course.delete')" link type="danger" @click="onDelete(row)"
            ><AppEmoji name="delete" size="sm" decorative />删除</el-button
          >
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

    <el-dialog v-model="dlg" :title="editId ? '编辑课程' : '新建课程'" width="560px">
      <el-form label-width="100px">
        <el-form-item v-if="!editId && auth.isAdmin && auth.can('field.course.enterprise')" label="所属企业" required>
          <el-select v-model="form.enterprise_id" placeholder="请选择企业" filterable style="width: 100%">
            <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editId && auth.can('field.course.enterprise')" label="所属企业">
          <el-input :model-value="editEnterpriseName" disabled />
        </el-form-item>
        <el-form-item v-if="auth.can('field.course.name')" label="课程名称" required>
          <el-input v-model="form.name" placeholder="课程名称" />
        </el-form-item>
        <el-form-item v-if="auth.can('field.course.instructor')" label="讲师" required>
          <el-input v-model="form.instructor" placeholder="讲师" />
        </el-form-item>
        <el-form-item v-if="auth.can('field.course.period')" label="课程期间" required>
          <el-date-picker
            v-model="periodRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item v-if="auth.can('field.course.description')" label="课程简介">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="课程简介" />
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
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { listEnterprises } from "@/api/enterprises";
import { listCourses, createCourse, patchCourse, deleteCourse } from "@/api/courses";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const searchKeyword = ref("");

const dlg = ref(false);
/** 日历区间，与 form.period_text 同步为「YYYY-MM-DD 至 YYYY-MM-DD」 */
const periodRange = ref<[string, string] | null>(null);
const editId = ref<number | null>(null);
const enterpriseOpts = ref<{ id: number; name: string }[]>([]);
const editEnterpriseName = ref("");

const form = reactive({
  name: "",
  instructor: "",
  period_text: "",
  description: "",
  enterprise_id: null as number | null,
});

watch(periodRange, (v) => {
  if (v && v[0] && v[1]) {
    form.period_text = `${v[0]} 至 ${v[1]}`;
  }
});

/** 从历史 period_text 中解析 YYYY-MM-DD，便于回显日历 */
function parsePeriodToRange(text: string): [string, string] | null {
  const dates = text.match(/\d{4}-\d{2}-\d{2}/g);
  if (!dates?.length) return null;
  if (dates.length >= 2) return [dates[0], dates[1]];
  return [dates[0], dates[0]];
}

function fmtTime(v: unknown) {
  if (!v) return "";
  return String(v).replace("T", " ").slice(0, 19);
}

async function load() {
  try {
    const skip = (page.value - 1) * limit.value;
    const kw = searchKeyword.value.trim();
    const { data } = await listCourses({
      skip,
      limit: limit.value,
      keyword: kw || undefined,
    });
    total.value = data.total;
    rows.value = data.items;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载失败"));
  }
}

function doSearch() {
  page.value = 1;
  load();
}

function openCreate() {
  editId.value = null;
  editEnterpriseName.value = "";
  form.name = "";
  form.instructor = "";
  form.period_text = "";
  periodRange.value = null;
  form.description = "";
  form.enterprise_id = enterpriseOpts.value[0]?.id ?? auth.me?.enterprise?.id ?? null;
  dlg.value = true;
}

function openEdit(row: Record<string, unknown>) {
  editId.value = row.id as number;
  form.name = (row.name as string) || "";
  form.instructor = (row.instructor as string) || "";
  form.period_text = (row.period_text as string) || "";
  periodRange.value = parsePeriodToRange(form.period_text);
  form.description = (row.description as string) || "";
  editEnterpriseName.value = ((row.enterprise as { name?: string } | null)?.name as string) || "";
  dlg.value = true;
}

async function save() {
  if (!periodRange.value || !periodRange.value[0] || !periodRange.value[1]) {
    ElMessage.warning("请选择课程期间（起止日期）");
    return;
  }
  form.period_text = `${periodRange.value[0]} 至 ${periodRange.value[1]}`;
  if (!form.name.trim() || !form.instructor.trim() || !form.period_text.trim()) {
    ElMessage.warning("请填写课程名称、讲师与课程期间");
    return;
  }
  try {
    if (!editId.value) {
      if (auth.isAdmin && (form.enterprise_id == null || form.enterprise_id < 1)) {
        ElMessage.warning("请选择所属企业");
        return;
      }
      const body: Record<string, unknown> = {
        name: form.name.trim(),
        instructor: form.instructor.trim(),
        period_text: form.period_text.trim(),
        description: form.description.trim() || null,
      };
      if (auth.isAdmin) body.enterprise_id = form.enterprise_id;
      await createCourse(body);
    } else {
      await patchCourse(editId.value, {
        name: form.name.trim(),
        instructor: form.instructor.trim(),
        period_text: form.period_text.trim(),
        description: form.description.trim() || null,
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
  await ElMessageBox.confirm("确定删除该课程？", "提示", { type: "warning" });
  await deleteCourse(row.id as number);
  ElMessage.success("已删除");
  await load();
}

onMounted(async () => {
  if (auth.isAdmin) {
    try {
      const { data: ent } = await listEnterprises({ skip: 0, limit: 200 });
      enterpriseOpts.value = ent.items.map((x: { id: number; name: string }) => ({ id: x.id, name: x.name }));
    } catch {
      enterpriseOpts.value = [];
    }
  }
  await load();
});
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
