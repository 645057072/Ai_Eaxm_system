<template>
  <el-card v-loading="loading" class="take-exam-card">
    <template #header>
      <div class="exam-hdr">
        <div class="exam-hdr-title">错题练习</div>
        <div class="exam-hdr-actions">
          <el-button @click="$router.back()"><AppEmoji name="back" size="sm" decorative />返回</el-button>
        </div>
      </div>
    </template>

    <div v-if="q" class="block">
      <div class="qhead">
        <span class="qstem">{{ q.stem }}（{{ qTypeLabel(q.q_type) }}）</span>
        <span class="remain-badge">剩余 {{ q.remaining }}</span>
      </div>

      <div v-if="!submitted">
        <template v-if="q.q_type === 'judge'">
          <el-radio-group v-model="ans">
            <el-radio :label="true">正确</el-radio>
            <el-radio :label="false">错误</el-radio>
          </el-radio-group>
        </template>
        <template v-else-if="q.q_type === 'single'">
          <el-radio-group v-model="ans">
            <el-radio v-for="opt in normOptions(q.options_json)" :key="opt.key" :label="opt.key"
              >{{ opt.key }}. {{ opt.text }}</el-radio
            >
          </el-radio-group>
        </template>
        <template v-else-if="q.q_type === 'multiple'">
          <el-checkbox-group v-model="ansMulti">
            <el-checkbox v-for="opt in normOptions(q.options_json)" :key="opt.key" :label="opt.key"
              >{{ opt.key }}. {{ opt.text }}</el-checkbox
            >
          </el-checkbox-group>
        </template>
        <template v-else>
          <el-input v-model="ansText" placeholder="请输入答案" />
        </template>

        <div class="ops">
          <el-button type="primary" :disabled="submitting" @click="onSubmit">
            <AppEmoji name="submitExam" size="sm" decorative />提交
          </el-button>
        </div>
      </div>

      <div v-else class="result">
        <el-alert :type="resultCorrect ? 'success' : 'error'" :closable="false">
          <template #title>{{ resultCorrect ? "回答正确，已从错题集中移除" : "回答错误，继续保留在错题集中" }}</template>
        </el-alert>
        <div class="kv">
          <div class="k">标准答案</div>
          <pre class="v">{{ formatStdAnswer(q, resultStd) }}</pre>
        </div>
        <div v-if="resultAnalysis" class="kv">
          <div class="k">解析</div>
          <pre class="v">{{ resultAnalysis }}</pre>
        </div>
        <div class="ops">
          <el-button type="primary" @click="next" :disabled="loading">
            <AppEmoji name="enterExam" size="sm" decorative />下一题
          </el-button>
        </div>
      </div>
    </div>

    <el-empty v-else-if="!loading" description="暂无错题，已全部练习完成" />
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { getNextWrongQuestion, submitWrongAnswer } from "@/api/wrong_practice";

const route = useRoute();
const courseId = Number(route.params.courseId);

type Q = {
  course_id: number;
  question_id: number;
  q_type: string;
  stem: string;
  options_json: unknown;
  remaining: number;
};

const loading = ref(false);
const submitting = ref(false);
const q = ref<Q | null>(null);

const ans = ref<unknown>(undefined);
const ansText = ref("");
const ansMulti = ref<string[]>([]);

const submitted = ref(false);
const resultCorrect = ref(false);
const resultStd = ref<unknown>(null);
const resultAnalysis = ref<string>("");

function qTypeLabel(t: string) {
  const m: Record<string, string> = { judge: "判断题", single: "单选题", multiple: "多选题", fill: "填空题" };
  return m[t] || t;
}

function normOptions(raw: unknown): { key: string; text: string }[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((x: Record<string, string>) => ({ key: String(x.key || x.label || ""), text: String(x.text || x.value || "") }));
}

function formatStdAnswer(q0: Q | null, std: unknown) {
  if (!q0) return String(std ?? "");
  const t = (q0.q_type || "").trim();
  if (t === "judge") {
    const s = String(std ?? "").trim().toLowerCase();
    if (std === true || s === "true" || s === "1" || s === "正确") return "正确";
    if (std === false || s === "false" || s === "0" || s === "错误") return "错误";
    return String(std ?? "");
  }
  const opts = normOptions(q0.options_json);
  const map = new Map(opts.map((o) => [o.key.toUpperCase(), o.text]));
  const lineOf = (k: string) => {
    const kk = k.trim().toUpperCase();
    const txt = map.get(kk) || "";
    return txt ? `${kk}. ${txt}` : kk;
  };
  if (t === "single") {
    const k = String(std ?? "").trim();
    return k ? lineOf(k) : "—";
  }
  if (t === "multiple") {
    const arr = Array.isArray(std) ? std : std == null ? [] : [std];
    const keys = arr.map((x) => String(x)).filter((x) => x.trim());
    if (!keys.length) return "—";
    return keys.map(lineOf).join("\n");
  }
  if (t === "fill") return String(std ?? "—");
  return String(std ?? "—");
}

function resetAnswerState() {
  ans.value = undefined;
  ansText.value = "";
  ansMulti.value = [];
  submitted.value = false;
  resultCorrect.value = false;
  resultStd.value = null;
  resultAnalysis.value = "";
}

const answerPayload = computed(() => {
  if (!q.value) return { question_id: 0, user_answer_json: null };
  if (q.value.q_type === "multiple") return { question_id: q.value.question_id, user_answer_json: ansMulti.value };
  if (q.value.q_type === "fill") return { question_id: q.value.question_id, user_answer_json: ansText.value };
  return { question_id: q.value.question_id, user_answer_json: ans.value };
});

async function loadNext() {
  loading.value = true;
  try {
    const { data } = await getNextWrongQuestion(courseId);
    q.value = data as Q;
    resetAnswerState();
  } catch (e) {
    q.value = null;
  } finally {
    loading.value = false;
  }
}

async function onSubmit() {
  if (!q.value) return;
  submitting.value = true;
  try {
    const { data } = await submitWrongAnswer(courseId, answerPayload.value);
    const d = data as { correct: boolean; std_answer_json: unknown; analysis?: string | null; remaining: number };
    resultCorrect.value = Boolean(d.correct);
    resultStd.value = d.std_answer_json;
    resultAnalysis.value = (d.analysis || "").trim();
    submitted.value = true;
    if (q.value) q.value.remaining = Number(d.remaining ?? q.value.remaining);
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "提交失败"));
  } finally {
    submitting.value = false;
  }
}

function next() {
  void loadNext();
}

onMounted(() => void loadNext());
</script>

<style scoped>
.take-exam-card :deep(.el-card__header) {
  padding: 12px 16px;
}
.exam-hdr {
  display: flex;
  align-items: center;
  min-height: 40px;
  position: relative;
}
.exam-hdr-title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  max-width: 60%;
  text-align: center;
  font-weight: 600;
  font-size: 16px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  pointer-events: none;
}
.exam-hdr-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
  align-items: center;
  z-index: 1;
}
.block {
  padding: 12px;
  background: #fff;
  border: 1px solid #eee;
}
.qhead {
  margin-bottom: 8px;
  font-weight: 500;
  line-height: 1.5;
  position: relative;
}
.remain-badge {
  position: absolute;
  right: 0;
  top: 0;
  font-size: 12px;
  color: #64748b;
  padding: 2px 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  border-radius: 999px;
}
.ops {
  margin-top: 12px;
  text-align: center;
}
.result {
  margin-top: 12px;
}
.kv {
  margin-top: 12px;
}
.k {
  font-size: 13px;
  color: #334155;
  margin-bottom: 6px;
  font-weight: 600;
}
.v {
  margin: 0;
  padding: 10px 12px;
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
  line-height: 1.45;
}
</style>

