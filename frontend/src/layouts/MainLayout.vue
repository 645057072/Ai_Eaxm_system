<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="brand">考试系统</div>
      <el-menu :default-active="route.path" router>
        <el-menu-item index="/">首页</el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/users">用户管理</el-menu-item>
        <el-menu-item v-if="auth.isTeacher" index="/questions">题库</el-menu-item>
        <el-menu-item v-if="auth.isTeacher" index="/papers">试卷</el-menu-item>
        <el-menu-item v-if="auth.isTeacher" index="/sessions">考试场次</el-menu-item>
        <el-menu-item v-if="auth.isStudent" index="/exam/available">可参加的考试</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="who">{{ auth.me?.username }}（{{ auth.me?.role?.name }}）</span>
        <el-button type="danger" link @click="onLogout">退出</el-button>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

function onLogout() {
  auth.logout();
  router.replace("/login");
}
</script>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  border-right: 1px solid #eee;
}
.brand {
  padding: 16px;
  font-weight: 600;
}
.header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  border-bottom: 1px solid #eee;
}
.who {
  color: #666;
}
.main {
  background: #fafafa;
}
</style>
