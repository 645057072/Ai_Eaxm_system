<template>
  <el-card>
    <div class="toolbar">
      <el-button type="success" @click="openCreate"><AppEmoji name="add" size="sm" decorative />新建试卷</el-button>
    </div>
    <el-table :data="rows">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="paper_no" label="试卷编号" width="150" show-overflow-tooltip />
      <el-table-column prop="title" label="试卷名称" min-width="140" show-overflow-tooltip />
      <el-table-column label="课程" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ (row.course_name as string) || "—" }}</template>
      </el-table-column>
      <el-table-column prop="paper_type" label="试卷类型" width="100" />
      <el-table-column label="等级" width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ (row.level_name as string) || "—" }}</template>
      </el-table-column>
      <el-table-column prop="duration_minutes" label="时长(分)" width="100" />
      <el-table-column prop="total_score" label="总分" width="90" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push('/papers/' + row.id)"
            ><AppEmoji name="compose" size="sm" decorative />组卷</el-button
          >
          <el-button link type="danger" @click="onDel(row)"><AppEmoji name="delete" size="sm" decorative />删除</el-button>
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

    <el-dialog v-model="dlg" title="新建试卷" width="820px" top="6vh">
      <el-form label-width="120px">
        <el-form-item label="试卷名称" required>
          <el-input v-model="form.title" placeholder="试卷名称" />
        </el-form-item>
        <el-form-item label="试卷编号">
          <el-input v-model="form.paper_no" clearable placeholder="留空则自动生成" />
        </el-form-item>
        <el-form-item label="关联课程" required>
          <el-select v-model="form.course_id" placeholder="选择课程（组卷题库区间）" filterable style="width: 100%">
            <el-option v-for="c in courseOpts" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="试卷类型">
          <el-select v-model="form.paper_type" style="width: 100%">
            <el-option label="正式" value="formal" />
            <el-option label="模拟" value="mock" />
            <el-option label="练习" value="practice" />
          </el-select>
        </el-form-item>
        <el-form-item label="试卷等级">
          <el-select v-model="form.level_id" clearable placeholder="可选" filterable style="width: 100%">
            <el-option v-for="lv in levelOpts" :key="lv.id" :label="`${lv.level_name}（${lv.level_code}）`" :value="lv.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="时长(分)">
          <el-input-number v-model="form.duration_minutes" :min="1" :max="600" />
        </el-form-item>
        <el-divider content-position="left">按题型抽题（题库区间为所选课程下已发布题目）</el-divider>
        <div class="rules-toolbar">
          <el-button type="primary" link @click="addRuleRow">增加题型行</el-button>
        </div>
        <el-table :data="ruleRows" border size="small" class="rules-table">
          <el-table-column label="题型" width="120">
            <template #default="{ row }">
              <el-select v-model="row.q_type" placeholder="题型" style="width: 100%">
                <el-option v-for="o in qTypeOpts" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="全选" width="72" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.use_all" />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.count" :min="0" :disabled="row.use_all" controls-position="right" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="自动拆分" width="110">
            <template #default="{ row }">
              <el-input-number v-model="row.auto_split" :min="1" controls-position="right" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="单题分值" width="110">
            <template #default="{ row }">
              <el-input-number v-model="row.score_per" :min="0" :step="0.5" controls-position="right" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link :disabled="ruleRows.length <= 1" @click="removeRuleRow($index)">删</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="saveCreate">创建</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { listPapers, createPaper, deletePaper } from "@/api/papers";
import { listCourses } from "@/api/courses";
import { listPaperLevels } from "@/api/paper_levels";

const router = useRouter();
const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const dlg = ref(false);
const form = reactive({
  title: "",
  paper_no: "",
  course_id: undefined as number | undefined,
  paper_type: "formal",
  level_id: undefined as number | undefined,
  description: "",
  duration_minutes: 60,
});

const courseOpts = ref<{ id: number; name: string }[]>([]);
const levelOpts = ref<{ id: number; level_name: string; level_code: string }[]>([]);

const qTypeOpts = [
  { value: "judge", label: "判断" },
  { value: "single", label: "单选" },
  { value: "multiple", label: "多选" },
  { value: "fill", label: "填空" },
];

interface RuleRow {
  q_type: string;
  use_all: boolean;
  count: number;
  auto_split: number;
  score_per: number;
}

function defaultRuleRow(): RuleRow {
  return {
    q_type: "single",
    use_all: false,
    count: 5,
    auto_split: 1,
    score_per: 1,
  };
}

const ruleRows = ref<RuleRow[]>([defaultRuleRow()]);

async function load() {
  const skip = (page.value - 1) * limit.value;
  const { data } = await listPapers({ skip, limit: limit.value });
  total.value = data.total;
  rows.value = data.items;
}

async function loadOpts() {
  const [cRes, lRes] = await Promise.all([
    listCourses({ skip: 0, limit: 500 }),
    listPaperLevels({ skip: 0, limit: 500 }),
  ]);
  courseOpts.value = (cRes.data.items || []) as { id: number; name: string }[];
  levelOpts.value = (lRes.data.items || []) as { id: number; level_name: string; level_code: string }[];
}

function openCreate() {
  form.title = "";
  form.paper_no = "";
  form.course_id = courseOpts.value[0]?.id;
  form.paper_type = "formal";
  form.level_id = undefined;
  form.description = "";
  form.duration_minutes = 60;
  ruleRows.value = [defaultRuleRow()];
  dlg.value = true;
}

function addRuleRow() {
  ruleRows.value.push(defaultRuleRow());
}

function removeRuleRow(i: number) {
  if (ruleRows.value.length <= 1) return;
  ruleRows.value.splice(i, 1);
}

async function saveCreate() {
  if (!form.title.trim()) {
    ElMessage.warning("请填写试卷名称");
    return;
  }
  if (!form.course_id) {
    ElMessage.warning("请选择关联课程");
    return;
  }
  const rulesPayload = ruleRows.value
    .filter((r) => r.q_type)
    .map((r) => ({
      q_type: r.q_type,
      use_all: r.use_all,
      count: r.use_all ? 0 : r.count,
      auto_split: r.auto_split,
      score_per: r.score_per,
    }));
  if (rulesPayload.length) {
    for (const r of rulesPayload) {
      if (!r.use_all && r.count < 1) {
        ElMessage.warning("未勾选全选时，每种题型数量至少为 1");
        return;
      }
    }
  }
  const body: Record<string, unknown> = {
    title: form.title.trim(),
    course_id: form.course_id,
    paper_type: form.paper_type,
    duration_minutes: form.duration_minutes,
    description: form.description.trim() || null,
    rules: rulesPayload,
  };
  const pn = form.paper_no.trim();
  if (pn) body.paper_no = pn;
  if (form.level_id) body.level_id = form.level_id;
  try {
    const { data } = await createPaper(body);
    ElMessage.success("已创建");
    dlg.value = false;
    await router.push("/papers/" + data.id);
  } catch {
    ElMessage.error("创建失败（请检查课程题库是否已有对应题型已发布题目）");
  }
}

async function onDel(row: Record<string, unknown>) {
  await ElMessageBox.confirm("确定删除该试卷？", "提示", { type: "warning" });
  await deletePaper(row.id as number);
  ElMessage.success("已删除");
  await load();
}

onMounted(async () => {
  await loadOpts();
  await load();
});
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.rules-toolbar {
  margin-bottom: 8px;
}
.rules-table {
  margin-bottom: 8px;
}
</style>
