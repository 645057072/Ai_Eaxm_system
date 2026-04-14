<template>
  <el-card v-loading="loading">
    <template #header>
      <div class="hdr">
        <span><AppEmoji name="papers" size="sm" decorative />试卷 #{{ id }} {{ paper?.title }}</span>
        <el-button @click="$router.back()"><AppEmoji name="back" size="sm" decorative />返回</el-button>
      </div>
    </template>
    <p class="meta">
      试卷编号：{{ paper?.paper_no || "—" }}；课程：{{ paper?.course_name || "—" }}；类型：{{
        paperTypeLabel(paper?.paper_type as string | undefined)
      }}；等级：{{ paper?.level_name || "—" }}
    </p>
    <p>时长：{{ paper?.duration_minutes }} 分钟，总分：{{ formatScore(paper?.total_score) }}（小题分值合计）</p>
    <div class="toolbar">
      <el-input-number v-model="addQid" :min="1" placeholder="题目ID" />
      <el-input-number v-model="addScore" :min="0" :step="0.5" />
      <el-input-number v-model="addOrder" :min="0" placeholder="排序号" />
      <el-button type="primary" @click="addItem"><AppEmoji name="addToPaper" size="sm" decorative />加入试卷</el-button>
    </div>
    <el-table :data="paper?.items || []" border class="items-table">
      <el-table-column label="序号" width="72" align="center">
        <template #default="{ $index }">{{ $index + 1 }}</template>
      </el-table-column>
      <el-table-column label="题号" width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ (row as PaperRow).question?.question_no || "—" }}</template>
      </el-table-column>
      <el-table-column label="题型" width="88">
        <template #default="{ row }">{{ qTypeLabel((row as PaperRow).question?.q_type) }}</template>
      </el-table-column>
      <el-table-column prop="score" label="分值" width="80" align="center" />
      <el-table-column prop="auto_split_count" label="拆分" width="72" align="center" />
      <el-table-column prop="question_id" label="题目ID" width="88" align="center" />
      <el-table-column label="题干" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ (row as PaperRow).question?.stem }}</template>
      </el-table-column>
      <el-table-column label="选项" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ formatOptions((row as PaperRow).question?.options_json) }}</template>
      </el-table-column>
      <el-table-column label="标准答案" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">
          {{
            formatAnswer(
              (row as PaperRow).question?.answer_json,
              (row as PaperRow).question?.q_type ?? "",
              (row as PaperRow).question?.options_json,
            )
          }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="danger" @click="remove(row)"><AppEmoji name="remove" size="sm" decorative />移除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { getPaper, addPaperItem, removePaperItem } from "@/api/papers";

const route = useRoute();
const id = Number(route.params.id);
const loading = ref(false);
const paper = ref<Record<string, unknown> | null>(null);
const addQid = ref(1);
const addScore = ref(1);
const addOrder = ref(1);

type QuestionBrief = {
  question_no?: string;
  q_type?: string;
  stem?: string;
  options_json?: unknown;
  answer_json?: unknown;
};

type PaperRow = {
  id: number;
  question_id: number;
  sort_order: number;
  score: number;
  question?: QuestionBrief | null;
};

const paperTypeLabelMap: Record<string, string> = {
  formal: "正式",
  mock: "模拟",
  practice: "练习",
};

function paperTypeLabel(code: string | undefined) {
  if (!code) return "—";
  return paperTypeLabelMap[code] ?? code;
}

const qTypeLabelMap: Record<string, string> = {
  judge: "判断",
  single: "单选",
  multiple: "多选",
  fill: "填空",
};

function qTypeLabel(q: string | undefined) {
  if (!q) return "—";
  return qTypeLabelMap[q] ?? q;
}

function formatScore(v: unknown) {
  if (v == null || v === "") return "0";
  const n = Number(v);
  return Number.isFinite(n) ? String(n) : String(v);
}

type OptItem = { key?: string; text?: string };

function formatOptions(opts: unknown): string {
  if (opts == null) return "—";
  if (!Array.isArray(opts)) {
    if (typeof opts === "object") return JSON.stringify(opts);
    return String(opts);
  }
  const lines = (opts as OptItem[])
    .map((o) => {
      const k = (o.key ?? "").trim();
      const t = (o.text ?? "").trim();
      return k ? `${k}. ${t}` : t;
    })
    .filter(Boolean);
  return lines.length ? lines.join("；") : "—";
}

function optionTextByKey(opts: unknown, key: string): string | null {
  if (!key || !Array.isArray(opts)) return null;
  const row = (opts as OptItem[]).find((o) => String(o.key ?? "").toUpperCase() === key.toUpperCase());
  const t = row?.text;
  return t != null && String(t).trim() !== "" ? String(t).trim() : null;
}

/** 标准答案展示：不含解析等非关键字段 */
function formatAnswer(ans: unknown, qType: string, options: unknown): string {
  if (ans == null) return "—";
  if (typeof ans === "string") return ans;
  if (typeof ans !== "object") return String(ans);
  const o = ans as Record<string, unknown>;
  if (qType === "judge") {
    const c = o.choice;
    if (c === "T" || c === true) return "正确";
    if (c === "F" || c === false) return "错误";
    return c != null ? String(c) : "—";
  }
  if (qType === "multiple") {
    const raw = o.choices;
    if (!Array.isArray(raw) || raw.length === 0) return JSON.stringify(ans);
    return raw
      .map((x) => String(x).toUpperCase())
      .map((k) => {
        const label = optionTextByKey(options, k);
        return label ? `${k}（${label}）` : k;
      })
      .join("、");
  }
  if (qType === "fill") {
    const t = o.text;
    return t != null && String(t) !== "" ? String(t) : "—";
  }
  const k = o.choice != null ? String(o.choice).toUpperCase() : "";
  if (!k) return "—";
  const label = optionTextByKey(options, k);
  return label ? `${k}（${label}）` : k;
}

function syncNextSortOrder() {
  const items = (paper.value?.items as PaperRow[] | undefined) || [];
  if (!items.length) {
    addOrder.value = 0;
    return;
  }
  const max = Math.max(...items.map((i) => Number(i.sort_order) || 0));
  addOrder.value = max + 1;
}

async function refresh() {
  loading.value = true;
  try {
    const { data } = await getPaper(id);
    paper.value = data as Record<string, unknown>;
    syncNextSortOrder();
  } finally {
    loading.value = false;
  }
}

watch(
  () => paper.value?.items,
  () => syncNextSortOrder(),
  { deep: true },
);

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
.meta {
  margin: 0 0 8px;
  font-size: 14px;
  color: #334155;
}
.items-table {
  width: 100%;
}
</style>
