<template>
  <el-card v-loading="loading" class="take-exam-card">
    <template #header>
      <div class="exam-hdr">
        <div class="exam-hdr-title">{{ title }}</div>
        <div class="exam-hdr-actions">
          <el-button v-if="isPractice" type="warning" :disabled="isSubmitting" @click="stageSave"
            ><AppEmoji name="save" size="sm" decorative />暂存</el-button
          >
          <el-button type="primary" :disabled="isSubmitting" @click="saveOnly"
            ><AppEmoji name="save" size="sm" decorative />保存答案</el-button
          >
          <el-button type="danger" :disabled="isSubmitting" @click="submit"
            ><AppEmoji name="submitExam" size="sm" decorative />交卷</el-button
          >
        </div>
      </div>
    </template>
    <div v-if="submittedTip" class="tip">{{ submittedTip }}</div>
    <div v-for="(q, qi) in questions" :key="q.question_id" class="block">
      <div class="qhead">
        <span class="qno">{{ qi + 1 }}.</span>
        <span class="qstem">{{ q.stem }}</span>
      </div>
      <div class="qtype-center">
        <span class="qtype-pill">{{ qTypeLabel(q.q_type) }}</span>
      </div>
      <template v-if="q.q_type === 'judge'">
        <el-radio-group v-model="answers[q.question_id]">
          <el-radio :label="true">正确</el-radio>
          <el-radio :label="false">错误</el-radio>
        </el-radio-group>
      </template>
      <template v-else-if="q.q_type === 'single'">
        <el-radio-group v-model="answers[q.question_id]">
          <el-radio v-for="opt in normOptions(q)" :key="opt.key" :label="opt.key">{{ opt.key }}. {{ opt.text }}</el-radio>
        </el-radio-group>
      </template>
      <template v-else-if="q.q_type === 'multiple'">
        <el-checkbox-group v-model="answers[q.question_id]">
          <el-checkbox v-for="opt in normOptions(q)" :key="opt.key" :label="opt.key">{{ opt.key }}. {{ opt.text }}</el-checkbox>
        </el-checkbox-group>
      </template>
      <template v-else>
        <el-input v-model="answers[q.question_id]" placeholder="请输入答案" />
      </template>
    </div>

    <el-dialog
      v-model="countdownVisible"
      title="重新开始作答"
      width="380px"
      :close-on-click-modal="false"
      :show-close="false"
      align-center
    >
      <p class="cd-text">{{ countdownSec }} 秒后可重新作答（答题区已清空）。</p>
    </el-dialog>

    <el-dialog
      v-model="submitCdVisible"
      title="正在交卷"
      width="380px"
      :close-on-click-modal="false"
      :show-close="false"
      align-center
    >
      <p class="cd-text">答案已保存，{{ submitCdSec }} 秒后自动交卷，交卷后不可继续作答。</p>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { getTakeData, startExam } from "@/api/sessions";
import { getAttempt, saveAnswers, stageAnswers, submitAttempt, restartPracticeAttempt } from "@/api/attempts";

type Q = {
  question_id: number;
  q_type: string;
  stem: string;
  options_json: unknown;
  score: string | number;
};

const route = useRoute();
const router = useRouter();
const sessionId = Number(route.params.sessionId);

const loading = ref(false);
const title = ref("");
const paperType = ref("formal");
const questions = ref<Q[]>([]);
const answers = reactive<Record<number, unknown>>({});
const attemptId = ref(0);
const submittedTip = ref("");
const isSubmitting = ref(false);

const isPractice = computed(() => paperType.value === "practice");

const countdownVisible = ref(false);
const countdownSec = ref(10);
const submitCdVisible = ref(false);
const submitCdSec = ref(3);

function qTypeLabel(t: string) {
  const m: Record<string, string> = {
    judge: "判断题",
    single: "单选题",
    multiple: "多选题",
    fill: "填空题",
  };
  return m[t] || t;
}

function normOptions(q: Q): { key: string; text: string }[] {
  const raw = q.options_json;
  if (!Array.isArray(raw)) return [];
  return raw.map((x: Record<string, string>) => ({
    key: String(x.key || x.label || ""),
    text: String(x.text || x.value || ""),
  }));
}

function initEmptyAnswers() {
  for (const q of questions.value) {
    if (q.q_type === "multiple") answers[q.question_id] = [];
    else answers[q.question_id] = undefined;
  }
}

function collectAnswersPayload() {
  return Object.keys(answers).map((k) => ({
    question_id: Number(k),
    user_answer_json: answers[Number(k)],
  }));
}

async function loadAnswersFromAttempt(aid: number) {
  initEmptyAnswers();
  const { data } = await getAttempt(aid);
  const list = (data as { answers?: { question_id: number; user_answer_json: unknown }[] }).answers || [];
  for (const a of list) {
    answers[a.question_id] = a.user_answer_json;
  }
}

async function runRestartCountdown() {
  countdownVisible.value = true;
  countdownSec.value = 10;
  await new Promise<void>((resolve) => {
    const t = setInterval(() => {
      countdownSec.value -= 1;
      if (countdownSec.value <= 0) {
        clearInterval(t);
        resolve();
      }
    }, 1000);
  });
  countdownVisible.value = false;
}

async function runSubmitCountdown() {
  submitCdVisible.value = true;
  submitCdSec.value = 3;
  await new Promise<void>((resolve) => {
    const t = setInterval(() => {
      submitCdSec.value -= 1;
      if (submitCdSec.value <= 0) {
        clearInterval(t);
        resolve();
      }
    }, 1000);
  });
  submitCdVisible.value = false;
}

async function boot() {
  loading.value = true;
  try {
    const td = (await getTakeData(sessionId)).data as {
      title: string;
      paper_type?: string;
      questions: Q[];
    };
    title.value = td.title;
    paperType.value = td.paper_type || "formal";
    questions.value = td.questions as Q[];

    const st = (await startExam(sessionId)).data as {
      attempt_id: number;
      status?: string;
      staged?: boolean;
    };
    attemptId.value = st.attempt_id;
    if (st.status === "submitted") {
      submittedTip.value = "本场考试已交卷，将跳转到成绩页。";
      await router.replace("/attempts/" + st.attempt_id);
      return;
    }

    if (paperType.value === "practice" && st.staged && st.status === "in_progress") {
      try {
        await ElMessageBox.confirm("考卷已暂存，是否继续作答？", "提示", {
          type: "info",
          confirmButtonText: "是",
          cancelButtonText: "否",
        });
        await loadAnswersFromAttempt(st.attempt_id);
      } catch {
        await restartPracticeAttempt(st.attempt_id);
        initEmptyAnswers();
        await runRestartCountdown();
      }
    } else {
      initEmptyAnswers();
    }
  } catch {
    ElMessage.error("无法进入考试（时间、发布状态等）");
    router.replace("/exam/available");
  } finally {
    loading.value = false;
  }
}

async function saveOnly() {
  const list = collectAnswersPayload();
  await saveAnswers(attemptId.value, list);
  ElMessage.success("答案已保存");
}

async function stageSave() {
  const list = collectAnswersPayload();
  await stageAnswers(attemptId.value, list);
  ElMessage.success("已暂存，下次进入可继续作答");
}

async function submit() {
  if (isSubmitting.value) return;
  try {
    await ElMessageBox.confirm("交卷后不可继续作答，是否确认？", "提示", { type: "warning" });
  } catch {
    return;
  }
  isSubmitting.value = true;
  try {
    await saveOnly();
    await runSubmitCountdown();
    await submitAttempt(attemptId.value);
    ElMessage.success("交卷成功");
    await router.replace("/attempts/" + attemptId.value);
  } catch (e) {
    ElMessage.error("交卷失败，请重试");
    console.error(e);
  } finally {
    isSubmitting.value = false;
  }
}

onMounted(boot);
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
  max-width: 50%;
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
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  z-index: 1;
}
.block {
  margin-bottom: 20px;
  padding: 12px;
  background: #fff;
  border: 1px solid #eee;
}
.qhead {
  margin-bottom: 8px;
  font-weight: 500;
  line-height: 1.5;
}
.qno {
  margin-right: 6px;
  font-weight: 600;
}
.qstem {
  white-space: pre-wrap;
}
.qtype-center {
  text-align: center;
  margin-bottom: 10px;
}
.qtype-pill {
  display: inline-block;
  padding: 2px 12px;
  font-size: 13px;
  color: #334155;
  background: #f1f5f9;
  border-radius: 999px;
  border: 1px solid #e2e8f0;
}
.tip {
  color: #e6a23c;
  margin-bottom: 12px;
}
.cd-text {
  text-align: center;
  font-size: 15px;
  margin: 8px 0 0;
}
</style>
