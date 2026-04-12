<template>
  <el-card class="home-card">
    <p class="lead">
      <AppEmoji name="welcome" size="md" decorative />
      欢迎使用在线考试系统。
    </p>
    <p v-if="auth.isTeacher" class="hint">
      <AppEmoji name="questionBank" size="sm" decorative />
      请从左侧进入「题库 / 试卷 / 考试场次」进行管理。
    </p>
    <p v-if="auth.isStudent" class="hint">
      <AppEmoji name="availableExams" size="sm" decorative />
      请从左侧进入「可参加的考试」开始答题。
    </p>
    <p v-if="auth.isAdmin" class="hint">
      <AppEmoji name="users" size="sm" decorative />
      您可使用「用户管理」维护账号与角色。
    </p>
  </el-card>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
</script>

<style scoped>
.home-card .lead {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  color: #1e293b;
  margin: 0 0 12px;
}
.hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 8px 0 0;
  color: #475569;
  line-height: 1.55;
}
</style>
