<template>
  <el-card>
    <p>欢迎使用在线考试系统。</p>
    <p v-if="auth.isTeacher">请从左侧进入「题库 / 试卷 / 考试场次」进行管理。</p>
    <p v-if="auth.isStudent">请从左侧进入「可参加的考试」开始答题。</p>
    <p v-if="auth.isAdmin">您可使用「用户管理」维护账号与角色。</p>
  </el-card>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
</script>
