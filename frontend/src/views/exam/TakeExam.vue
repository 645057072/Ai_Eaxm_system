<template>
  <el-card v-loading="loading" class="take-exam-card" :class="{ obfuscate: obfuscate }">
    <template #header>
      <div class="exam-hdr">
        <h2 class="exam-hdr-title">{{ title }}</h2>
        <div class="exam-hdr-actions">
          <div v-if="durationMinutes" class="exam-timer">
            <span class="timer-item">考试时间：{{ durationMinutes }} 分钟</span>
            <span class="timer-sep">|</span>
            <span class="timer-item">剩余：{{ fmtRemain(remainingSec) }}</span>
          </div>
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
        <span class="qstem">{{ q.stem }}（{{ qTypeLabel(q.q_type) }}）</span>
      </div>
      <template v-if="q.q_type === 'judge'">
        <el-radio-group v-model="answers[q.question_id]">
          <el-radio :value="true">正确</el-radio>
          <el-radio :value="false">错误</el-radio>
        </el-radio-group>
      </template>
      <template v-else-if="q.q_type === 'single'">
        <el-radio-group v-model="answers[q.question_id]">
          <el-radio v-for="opt in normOptions(q)" :key="opt.key" :value="opt.key">{{ opt.key }}. {{ opt.text }}</el-radio>
        </el-radio-group>
      </template>
      <template v-else-if="q.q_type === 'multiple'">
        <el-checkbox-group v-model="answers[q.question_id]">
          <el-checkbox v-for="opt in normOptions(q)" :key="opt.key" :value="opt.key">{{ opt.key }}. {{ opt.text }}</el-checkbox>
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
import { computed, onMounted, onUnmounted, reactive, ref } from "vue";
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
const durationMinutes = ref<number | null>(null);
/** 本次考试时长起算时刻（毫秒时间戳），与 started_at 区分，用于续考倒计时 */
const timerStartedAtMs = ref<number | null>(null);
const remainingSec = ref(0);
let remainTimer: ReturnType<typeof setInterval> | null = null;
/** 考试时间耗尽后仅触发一次自动交卷，避免重复提交 */
const autoSubmitDone = ref(false);
const formalLocked = ref(false);
const obfuscate = ref(false);
let obfuscateTimer: ReturnType<typeof setTimeout> | null = null;
let warnAt = 0;

const isPractice = computed(() => paperType.value === "practice");
const isFormal = computed(() => paperType.value === "formal");

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

/** 与服务端 exam_timer_started_at 对齐（练习卷重新开始作答后须刷新倒计时起点） */
async function syncTimerFromAttempt(aid: number) {
  const { data } = await getAttempt(aid);
  const d = data as { exam_timer_started_at?: string; started_at?: string };
  let t0 = parseStartedAtMs(d.exam_timer_started_at);
  if (t0 == null) {
    t0 = parseStartedAtMs(d.started_at);
  }
  timerStartedAtMs.value = t0;
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

function fmtRemain(sec: number) {
  const s = Math.max(0, Math.floor(sec));
  const hh = String(Math.floor(s / 3600)).padStart(2, "0");
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

/** 是否含 ISO 时区后缀（Z 或 ±hh:mm） */
function hasExplicitTimeZone(s: string): boolean {
  return /[zZ]$|[+-]\d{2}:\d{2}$/.test(s.trim());
}

/**
 * 解析后端返回的开始时刻（毫秒）。
 * 后端存 UTC，MySQL/Pydantic 常序列化为无时区 ISO；浏览器会当作「本地时间」解析，在东八区等会导致时间偏早约 8 小时，
 * 剩余时间瞬间为 0 并误触自动交卷。无时区后缀时按 UTC 解析。
 */
function parseStartedAtMs(raw: unknown): number | null {
  if (raw == null) return null;
  if (typeof raw === "number" && Number.isFinite(raw)) return raw;
  const s0 = String(raw).trim();
  if (!s0) return null;

  const isoNoTz = /^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(\.\d+)?$/.exec(s0);
  if (isoNoTz && !hasExplicitTimeZone(s0)) {
    const frac = isoNoTz[3] || "";
    const tUtc = new Date(`${isoNoTz[1]}T${isoNoTz[2]}${frac}Z`).getTime();
    if (Number.isFinite(tUtc)) return tUtc;
  }

  let t = new Date(s0).getTime();
  if (Number.isFinite(t)) return t;
  const m = s0.match(/^(\d{4}-\d{2}-\d{2})[\sT](\d{2}:\d{2}:\d{2})/);
  if (m) {
    t = new Date(`${m[1]}T${m[2]}Z`).getTime();
    if (Number.isFinite(t)) return t;
  }
  return null;
}

function coerceDurationMinutes(v: unknown, fallback: unknown): number | null {
  const a = Number(v);
  if (Number.isFinite(a) && a > 0) return Math.floor(a);
  const b = Number(fallback);
  if (Number.isFinite(b) && b > 0) return Math.floor(b);
  return null;
}

function updateRemaining() {
  const dur = durationMinutes.value;
  const t0 = timerStartedAtMs.value;
  if (!dur || t0 == null) return;
  // 起算时间略晚于客户端时钟时 used 为负，按 0 处理，避免误判已超时
  const used = Math.max(0, Math.floor((Date.now() - t0) / 1000));
  const next = Math.max(0, dur * 60 - used);
  remainingSec.value = next;
  if (next > 0) return;
  if (autoSubmitDone.value || isSubmitting.value || !attemptId.value || loading.value) return;
  void autoSubmitOnTimeout();
}

/** 考试时长用尽：静默保存并交卷（不弹确认、不等待人工倒计时） */
async function autoSubmitOnTimeout() {
  if (autoSubmitDone.value || isSubmitting.value || !attemptId.value) return;
  autoSubmitDone.value = true;
  if (remainTimer) {
    clearInterval(remainTimer);
    remainTimer = null;
  }
  isSubmitting.value = true;
  try {
    ElMessage.warning("考试时间已到，系统正在自动交卷…");
    const list = collectAnswersPayload();
    await saveAnswers(attemptId.value, list);
    await submitAttempt(attemptId.value);
    ElMessage.success("已自动交卷");
    setFormalLock(false);
    await router.replace("/attempts/" + attemptId.value);
  } catch (e) {
    autoSubmitDone.value = false;
    ElMessage.error("自动交卷失败，请尽快手动交卷");
    console.error(e);
  } finally {
    isSubmitting.value = false;
  }
}

function startRemainCountdown() {
  if (remainTimer) {
    clearInterval(remainTimer);
    remainTimer = null;
  }
  if (!durationMinutes.value || timerStartedAtMs.value == null) return;
  updateRemaining();
  remainTimer = setInterval(updateRemaining, 1000);
}

function setFormalLock(on: boolean) {
  formalLocked.value = on;
  if (on) localStorage.setItem("formal_exam_lock", String(attemptId.value || "1"));
  else localStorage.removeItem("formal_exam_lock");
}

function bindFormalGuards() {
  const warn = (msg: string) => {
    const now = Date.now();
    if (now - warnAt < 2500) return;
    warnAt = now;
    ElMessage.warning(msg);
  };
  const obf = () => {
    obfuscate.value = true;
    if (obfuscateTimer) window.clearTimeout(obfuscateTimer);
    obfuscateTimer = window.setTimeout(() => {
      obfuscate.value = false;
      obfuscateTimer = null;
    }, 2500);
  };
  const onVis = () => {
    if (document.hidden) {
      warn("正式考试进行中，请勿切换页面/页签");
      obf();
    }
  };
  const onFs = () => {
    if (!document.fullscreenElement) {
      warn("正式考试进行中，请保持全屏");
      obf();
    }
  };
  const onBlur = () => {
    warn("正式考试进行中，请保持考试窗口在最前");
    obf();
  };
  const onResize = () => {
    if (window.innerHeight < 200 || window.innerWidth < 400) {
      warn("正式考试进行中，请勿最小化或异常缩放窗口");
      obf();
    }
  };
  document.addEventListener("visibilitychange", onVis);
  document.addEventListener("fullscreenchange", onFs);
  window.addEventListener("blur", onBlur);
  window.addEventListener("resize", onResize);
  return () => {
    document.removeEventListener("visibilitychange", onVis);
    document.removeEventListener("fullscreenchange", onFs);
    window.removeEventListener("blur", onBlur);
    window.removeEventListener("resize", onResize);
  };
}

let unbindFormal: (() => void) | null = null;
let unbindCopyGuards: (() => void) | null = null;

function bindNoCopyGuards() {
  const warn = () => ElMessage.warning("考试中禁止复制题干内容");
  const onCopy = (e: ClipboardEvent) => {
    e.preventDefault();
    warn();
  };
  const onCut = (e: ClipboardEvent) => {
    e.preventDefault();
    warn();
  };
  const onCtx = (e: MouseEvent) => {
    const el = e.target as HTMLElement | null;
    if (!el) return;
    if (el.closest(".take-exam-card")) {
      e.preventDefault();
      warn();
    }
  };
  const onKey = (e: KeyboardEvent) => {
    const k = e.key.toLowerCase();
    if ((e.ctrlKey || e.metaKey) && (k === "c" || k === "x" || k === "a")) {
      e.preventDefault();
      warn();
    }
  };
  document.addEventListener("copy", onCopy);
  document.addEventListener("cut", onCut);
  document.addEventListener("contextmenu", onCtx);
  window.addEventListener("keydown", onKey, true);
  return () => {
    document.removeEventListener("copy", onCopy);
    document.removeEventListener("cut", onCut);
    document.removeEventListener("contextmenu", onCtx);
    window.removeEventListener("keydown", onKey, true);
  };
}

async function boot() {
  loading.value = true;
  let startTimerAfterBoot = false;
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
      started_at?: string;
      timer_started_at?: string;
      duration_minutes?: number;
    };
    attemptId.value = st.attempt_id;
    durationMinutes.value = coerceDurationMinutes(st.duration_minutes, td.duration_minutes);
    let t0 = parseStartedAtMs(st.timer_started_at);
    if (t0 == null) {
      t0 = parseStartedAtMs(st.started_at);
    }
    timerStartedAtMs.value = t0;
    if (st.status === "submitted") {
      submittedTip.value = "本场考试已交卷，将跳转到成绩页。";
      await router.replace("/attempts/" + st.attempt_id);
      return;
    }

    // 正式考试：锁定导航并要求全屏（尽量约束）
    if (isFormal.value) {
      setFormalLock(true);
      try {
        await document.documentElement.requestFullscreen();
      } catch {
        // 不做兜底
      }
      if (unbindFormal) unbindFormal();
      unbindFormal = bindFormalGuards();
      if (unbindCopyGuards) unbindCopyGuards();
      unbindCopyGuards = bindNoCopyGuards();
    } else {
      setFormalLock(false);
      if (unbindCopyGuards) {
        unbindCopyGuards();
        unbindCopyGuards = null;
      }
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
        await syncTimerFromAttempt(st.attempt_id);
        await runRestartCountdown();
      }
    } else {
      initEmptyAnswers();
    }
    startTimerAfterBoot = !!(durationMinutes.value && timerStartedAtMs.value != null);
  } catch {
    ElMessage.error("无法进入考试（时间、发布状态等）");
    router.replace("/exam/available");
  } finally {
    loading.value = false;
    if (startTimerAfterBoot) {
      startRemainCountdown();
    }
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
    setFormalLock(false);
    await router.replace("/attempts/" + attemptId.value);
  } catch (e) {
    ElMessage.error("交卷失败，请重试");
    console.error(e);
  } finally {
    isSubmitting.value = false;
  }
}

onMounted(boot);
onUnmounted(() => {
  if (remainTimer) clearInterval(remainTimer);
  remainTimer = null;
  if (unbindFormal) unbindFormal();
  unbindFormal = null;
  if (unbindCopyGuards) unbindCopyGuards();
  unbindCopyGuards = null;
  if (obfuscateTimer) window.clearTimeout(obfuscateTimer);
  obfuscateTimer = null;
  setFormalLock(false);
});
</script>

<style scoped>
/* 低于系统顶栏 z-index(100)，高于题目卡片，避免与导航栏错误叠层 */
.take-exam-card :deep(.el-card__header) {
  padding: 12px 16px;
  position: sticky;
  top: 0;
  z-index: 40;
  background: #fff;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.06);
}
.take-exam-card {
  overflow: visible;
}
.take-exam-card :deep(.el-card__body) {
  overflow: visible;
}
/* 标题独占一行可换行；计时与按钮下一行右对齐，避免长标题与计时器重叠 */
.exam-hdr {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
}
.exam-hdr-title {
  margin: 0;
  font-weight: 600;
  font-size: 16px;
  line-height: 1.45;
  color: #0f172a;
  word-break: break-word;
  overflow-wrap: anywhere;
  text-align: left;
}
/* 宽屏：标题与操作区同一行，标题自适应剩余空间，操作区不挤压换行 */
@media (min-width: 960px) {
  .exam-hdr {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px 16px;
  }
  .exam-hdr-title {
    flex: 1 1 200px;
    min-width: 0;
    max-width: 100%;
  }
  .exam-hdr-actions {
    flex: 0 1 auto;
    justify-content: flex-end;
  }
}
.exam-hdr-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}
.exam-timer {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  row-gap: 4px;
  font-size: 13px;
  color: #334155;
  padding: 6px 10px;
  min-height: 32px;
  box-sizing: border-box;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  border-radius: 6px;
}
.timer-sep {
  color: #94a3b8;
}
.block {
  margin-bottom: 20px;
  padding: 12px;
  background: #fff;
  border: 1px solid #eee;
  /* 粘性考试头栏遮挡题干时，滚动锚点留出顶部空隙 */
  scroll-margin-top: 120px;
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
.take-exam-card :deep(.qstem),
.take-exam-card :deep(.block) {
  -webkit-user-select: none;
  user-select: none;
}
.take-exam-card.obfuscate :deep(.qstem) {
  filter: blur(5px);
  text-shadow: 0 0 6px rgba(0, 0, 0, 0.7);
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
