<template>
  <el-container class="layout">
    <el-aside width="228px" class="aside">
      <div class="brand">
        <AppEmoji name="brand" size="lg" decorative />
        <span class="brand-text">考试系统</span>
      </div>
      <el-menu :default-active="route.path" router>
        <el-menu-item index="/">
          <span class="menu-item-inner"><AppEmoji name="home" size="sm" decorative />首页</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/users">
          <span class="menu-item-inner"><AppEmoji name="users" size="sm" decorative />用户管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isTeacher" index="/questions">
          <span class="menu-item-inner"><AppEmoji name="questionBank" size="sm" decorative />题库</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isTeacher" index="/papers">
          <span class="menu-item-inner"><AppEmoji name="papers" size="sm" decorative />试卷</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isTeacher" index="/sessions">
          <span class="menu-item-inner"><AppEmoji name="sessions" size="sm" decorative />考试场次</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isStudent" index="/exam/available">
          <span class="menu-item-inner"><AppEmoji name="availableExams" size="sm" decorative />可参加的考试</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="who">
          <AppEmoji name="user" size="sm" decorative />
          {{ auth.me?.username }}（{{ auth.me?.role?.name }}）
        </span>
        <el-button type="danger" link @click="onLogout">
          <AppEmoji name="logout" size="sm" decorative />退出
        </el-button>
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
  border-right: 1px solid #e4e8ef;
  background: linear-gradient(180deg, #fbfcfe 0%, #f3f5f9 100%);
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
  font-weight: 600;
  font-size: 16px;
  color: #1e293b;
  border-bottom: 1px solid #e8ecf2;
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 55%);
}
.brand-text {
  letter-spacing: 0.02em;
}
.header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  border-bottom: 1px solid #e8ecf2;
  background: #fff;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
}
.who {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #475569;
  font-size: 14px;
}
</style>
