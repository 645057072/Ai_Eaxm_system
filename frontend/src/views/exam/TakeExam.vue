<template>
  <el-card v-loading="loading">
    <template #header>
      <div class="hdr">
        <span>{{ title }}</span>
        <el-button type="primary" @click="saveOnly"><AppEmoji name="save" size="sm" decorative />保存答案</el-button>
        <el-button type="danger" @click="submit"><AppEmoji name="submitExam" size="sm" decorative />交卷</el-button>
      </div>
    </template>
    <div v-if="submittedTip" class="tip">{{ submittedTip }}</div>
    <div v-for="q in questions" :key="q.question_id" class="block">
      <div class="qhead">（{{ q.q_type }}，{{ q.score }} 分）{{ q.stem }}</div>
      <!-- 判断 -->
      <template v-if="q.q_type === 'judge'">
        <el-radio-group v-model="answers[q.question_id]">
          <el-radio :label="true">正确</el-radio>
          <el-radio :label="false">错误</el-radio>
        </el-radio-group>
      </template>
      <!-- 单选 -->
      <template v-else-if="q.q_type === 'single'">
        <el-radio-group v-model="answers[q.question_id]">
          <el-radio v-for="opt in normOptions(q)" :key="opt.key" :label="opt.key">{{ opt.key }}. {{ opt.text }}</el-radio>
        </el-radio-group>
      </template>
      <!-- 多选 -->
      <template v-else-if="q.q_type === 'multiple'">
        <el-checkbox-group v-model="answers[q.question_id]">
          <el-checkbox v-for="opt in normOptions(q)" :key="opt.key" :label="opt.key">{{ opt.key }}. {{ opt.text }}</el-checkbox>
        </el-checkbox-group>
      </template>
      <!-- 填空 -->
      <template v-else>
        <el-input v-model="answers[q.question_id]" placeholder="请输入答案" />
      </template>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { getTakeData, startExam } from "@/api/sessions";
import { saveAnswers, submitAttempt } from "@/api/attempts";

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
const questions = ref<Q[]>([]);
const answers = reactive<Record<number, unknown>>({});
const attemptId = ref(0);
const submittedTip = ref("");

function normOptions(q: Q): { key: string; text: string }[] {
  const raw = q.options_json;
  if (!Array.isArray(raw)) return [];
  return raw.map((x: Record<string, string>) => ({
    key: String(x.key || x.label || ""),
    text: String(x.text || x.value || ""),
  }));
}

async function boot() {
  loading.value = true;
  try {
    const td = (await getTakeData(sessionId)).data;
    title.value = td.title;
    questions.value = td.questions as Q[];
    for (const q of questions.value) {
      if (q.q_type === "multiple") answers[q.question_id] = [];
      else answers[q.question_id] = undefined;
    }
    const st = (await startExam(sessionId)).data;
    attemptId.value = st.attempt_id;
    if (st.status === "submitted") {
      submittedTip.value = "本场考试已交卷，将跳转到成绩页。";
      await router.replace("/attempts/" + st.attempt_id);
      return;
    }
  } catch {
    ElMessage.error("无法进入考试（时间、发布状态等）");
    router.replace("/exam/available");
  } finally {
    loading.value = false;
  }
}

async function saveOnly() {
  const list = Object.keys(answers).map((k) => ({
    question_id: Number(k),
    user_answer_json: answers[Number(k)],
  }));
  await saveAnswers(attemptId.value, list);
  ElMessage.success("答案已保存");
}

async function submit() {
  await ElMessageBox.confirm("交卷后不可修改，是否确认？", "提示", { type: "warning" });
  await saveOnly();
  await submitAttempt(attemptId.value);
  ElMessage.success("交卷成功");
  await router.replace("/attempts/" + attemptId.value);
}

onMounted(boot);
</script>

<style scoped>
.hdr {
  display: flex;
  gap: 8px;
  align-items: center;
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
}
.tip {
  color: #e6a23c;
  margin-bottom: 12px;
}
</style>
