<template>
  <el-card>
    <div class="toolbar">
      <el-select v-model="filterType" clearable placeholder="题型" style="width: 140px">
        <el-option label="判断" value="judge" />
        <el-option label="单选" value="single" />
        <el-option label="多选" value="multiple" />
        <el-option label="填空" value="fill" />
      </el-select>
      <el-select v-model="filterStatus" clearable placeholder="状态" style="width: 140px">
        <el-option label="草稿" value="draft" />
        <el-option label="已发布" value="published" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openEdit()">新建题目</el-button>
    </div>
    <el-table :data="rows">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="q_type" label="题型" width="90" />
      <el-table-column prop="stem" label="题干" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="90" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="onDel(row)">删除</el-button>
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

    <el-dialog v-model="dlg" :title="form.id ? '编辑题目' : '新建题目'" width="640px">
      <el-form label-width="100px">
        <el-form-item label="题型">
          <el-select v-model="form.q_type" style="width: 100%">
            <el-option label="判断 judge" value="judge" />
            <el-option label="单选 single" value="single" />
            <el-option label="多选 multiple" value="multiple" />
            <el-option label="填空 fill" value="fill" />
          </el-select>
        </el-form-item>
        <el-form-item label="题干"><el-input v-model="form.stem" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="选项 JSON"
          ><el-input v-model="optionsText" type="textarea" :rows="4" placeholder='如 [{"key":"A","text":"..."}]'
        /></el-form-item>
        <el-form-item label="答案 JSON"
          ><el-input v-model="answerText" type="textarea" :rows="3" placeholder="见详设说明"
        /></el-form-item>
        <el-form-item label="解析"><el-input v-model="form.analysis" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="难度(1-5)"><el-input-number v-model="form.difficulty" :min="1" :max="5" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="草稿 draft" value="draft" />
            <el-option label="已发布 published" value="published" />
          </el-select>
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
import { listQuestions, createQuestion, updateQuestion, deleteQuestion } from "@/api/questions";

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);
const filterType = ref<string | undefined>();
const filterStatus = ref<string | undefined>();

const dlg = ref(false);
const optionsText = ref("");
const answerText = ref("");
const form = reactive({
  id: 0,
  q_type: "single",
  stem: "",
  options_json: null as unknown,
  answer_json: null as unknown,
  analysis: "",
  difficulty: 1,
  status: "draft",
});

watch(optionsText, (v) => {
  if (!v.trim()) {
    form.options_json = null;
    return;
  }
  try {
    form.options_json = JSON.parse(v);
  } catch {
    /* 保存时再校验 */
  }
});
watch(answerText, (v) => {
  try {
    form.answer_json = JSON.parse(v);
  } catch {
    form.answer_json = v;
  }
});

async function load() {
  const skip = (page.value - 1) * limit.value;
  const { data } = await listQuestions({
    skip,
    limit: limit.value,
    q_type: filterType.value,
    status: filterStatus.value,
  });
  total.value = data.total;
  rows.value = data.items;
}

function openEdit(row?: Record<string, unknown>) {
  if (!row) {
    form.id = 0;
    form.q_type = "single";
    form.stem = "";
    form.analysis = "";
    form.difficulty = 1;
    form.status = "draft";
    optionsText.value = "";
    answerText.value = "";
    form.options_json = null;
    form.answer_json = null;
  } else {
    form.id = row.id as number;
    form.q_type = row.q_type as string;
    form.stem = row.stem as string;
    form.analysis = (row.analysis as string) || "";
    form.difficulty = row.difficulty as number;
    form.status = row.status as string;
    optionsText.value = row.options_json ? JSON.stringify(row.options_json, null, 2) : "";
    answerText.value =
      typeof row.answer_json === "string" ? row.answer_json : JSON.stringify(row.answer_json, null, 2);
    form.answer_json = row.answer_json;
    form.options_json = row.options_json;
  }
  dlg.value = true;
}

async function save() {
  try {
    if (optionsText.value.trim()) form.options_json = JSON.parse(optionsText.value);
    else form.options_json = null;
    if (answerText.value.trim().startsWith("{") || answerText.value.trim().startsWith("["))
      form.answer_json = JSON.parse(answerText.value);
    else form.answer_json = answerText.value;
  } catch {
    ElMessage.error("选项或答案 JSON 格式不正确");
    return;
  }
  const body = {
    q_type: form.q_type,
    stem: form.stem,
    options_json: form.options_json,
    answer_json: form.answer_json,
    analysis: form.analysis || null,
    difficulty: form.difficulty,
    status: form.status,
  };
  try {
    if (!form.id) await createQuestion(body);
    else await updateQuestion(form.id, body);
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch {
    ElMessage.error("保存失败");
  }
}

async function onDel(row: Record<string, unknown>) {
  await ElMessageBox.confirm("确定删除？", "提示", { type: "warning" });
  await deleteQuestion(row.id as number);
  ElMessage.success("已删除");
  await load();
}

onMounted(load);
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
