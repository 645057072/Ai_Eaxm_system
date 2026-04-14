<template>
  <div class="fill-height">
    <el-card v-loading="loading" class="page-list-card paper-detail-page">
      <template #header>
        <div class="hdr page-list-card-title">
          <span><AppEmoji name="papers" size="sm" decorative />试卷组卷 #{{ id }} {{ paper?.title }}</span>
          <el-button @click="$router.back()"><AppEmoji name="back" size="sm" decorative />返回</el-button>
        </div>
      </template>
      <div class="page-list-sticky-block">
        <p class="meta">
          试卷编号：{{ paper?.paper_no || "—" }}；课程：{{ paper?.course_name || "—" }}；类型：{{
            paperTypeLabel(paper?.paper_type as string | undefined)
          }}；等级：{{ paper?.level_name || "—" }}
        </p>
        <p class="meta meta-second">时长：{{ paper?.duration_minutes }} 分钟，总分：{{ formatScore(paper?.total_score) }}（小题分值合计）</p>
        <div class="page-list-toolbar toolbar">
          <el-input-number v-model="addQid" :min="1" placeholder="题目ID" />
          <el-input-number v-model="addScore" :min="0" :step="0.5" />
          <el-input-number v-model="addOrder" :min="0" placeholder="排序号" />
          <el-button type="primary" @click="addItem"><AppEmoji name="addToPaper" size="sm" decorative />加入试卷</el-button>
        </div>
      </div>
      <div class="page-list-body">
        <div class="page-list-table">
          <el-table :data="sortedPaperItems" border class="items-table" height="100%">
            <el-table-column label="编号" width="72" align="center">
              <template #default="{ row }">{{ typeSerialByItemId.get((row as PaperRow).id) ?? "—" }}</template>
            </el-table-column>
            <el-table-column label="题库题号" width="120" show-overflow-tooltip>
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
            <el-table-column label="标准答案" min-width="100" show-overflow-tooltip>
              <template #default="{ row }">
                {{ formatAnswerShort((row as PaperRow).question?.answer_json, (row as PaperRow).question?.q_type ?? "") }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button link type="danger" @click="remove(row)"><AppEmoji name="remove" size="sm" decorative />移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
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

const qtypeRank: Record<string, number> = { judge: 0, single: 1, multiple: 2, fill: 3 };

/** 按题型升序、同题型题库题号升序，与业务展示一致 */
const sortedPaperItems = computed(() => {
  const items = (paper.value?.items as PaperRow[]) ?? [];
  return [...items].sort((a, b) => {
    const qa = a.question?.q_type ?? "";
    const qb = b.question?.q_type ?? "";
    const ra = qtypeRank[qa] ?? 99;
    const rb = qtypeRank[qb] ?? 99;
    if (ra !== rb) return ra - rb;
    const na = (a.question?.question_no ?? "").trim();
    const nb = (b.question?.question_no ?? "").trim();
    const cmp = na.localeCompare(nb, undefined, { numeric: true, sensitivity: "base" });
    if (cmp !== 0) return cmp;
    return (a.sort_order ?? 0) - (b.sort_order ?? 0);
  });
});

/** 各题型内从 1 递增的展示编号 */
const typeSerialByItemId = computed(() => {
  const m = new Map<number, number>();
  const counts = new Map<string, number>();
  for (const it of sortedPaperItems.value) {
    const qt = it.question?.q_type ?? "_";
    const next = (counts.get(qt) ?? 0) + 1;
    counts.set(qt, next);
    m.set(it.id, next);
  }
  return m;
});

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

/** 标准答案仅显示选项键：判断 T/F，单选 A，多选 ABC（无说明文字） */
function formatAnswerShort(ans: unknown, qType: string): string {
  if (ans == null) return "—";
  if (typeof ans === "string") {
    const s = ans.trim();
    if (qType === "judge") {
      if (s === "正确" || s.toUpperCase() === "T") return "T";
      if (s === "错误" || s.toUpperCase() === "F") return "F";
      return s;
    }
    if (qType === "single") {
      const m = s.match(/^([A-Za-z])\s*[（(]?/);
      if (m) return m[1].toUpperCase();
      return s;
    }
    if (qType === "multiple") {
      const compact = s.replace(/\s/g, "");
      if (/^[A-Za-z]{2,}$/.test(compact)) {
        return [...compact.toUpperCase()]
          .filter((ch, i, arr) => arr.indexOf(ch) === i)
          .sort()
          .join("");
      }
      const parts = s.split(/[;；,，]+/).map((p) => p.trim()).filter(Boolean);
      const keys: string[] = [];
      for (const p of parts) {
        const m = p.match(/^([A-Za-z])/);
        if (m) keys.push(m[1].toUpperCase());
      }
      if (keys.length) return [...new Set(keys)].sort().join("");
      return s;
    }
    return s;
  }
  if (typeof ans !== "object") return String(ans);
  const o = ans as Record<string, unknown>;
  if (qType === "judge") {
    const c = o.choice;
    if (c === "T" || c === true || c === "正确") return "T";
    if (c === "F" || c === false || c === "错误") return "F";
    if (typeof c === "string") {
      const u = c.trim().toUpperCase();
      if (u === "T" || u === "F") return u;
    }
    return "—";
  }
  if (qType === "multiple") {
    const raw = o.choices;
    if (!Array.isArray(raw) || raw.length === 0) return "—";
    return [...raw].map((x) => String(x).toUpperCase()).sort().join("");
  }
  if (qType === "fill") {
    const t = o.text;
    return t != null && String(t) !== "" ? String(t) : "—";
  }
  const k = o.choice != null ? String(o.choice).toUpperCase() : "";
  return k || "—";
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
  width: 100%;
}
.toolbar {
  margin-bottom: 0;
}
.meta {
  margin: 0 0 6px;
  font-size: 14px;
  color: #334155;
}
.meta-second {
  margin-bottom: 10px;
}
.items-table {
  width: 100%;
}
.paper-detail-page :deep(.el-card__header) {
  padding: 12px 16px;
}
</style>
