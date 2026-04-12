<template>
  <el-container class="layout">
    <el-aside width="256px" class="aside">
      <div class="brand">
        <AppEmoji name="brand" size="lg" decorative />
        <span class="brand-text">考试系统</span>
      </div>
      <el-menu :default-active="route.path" router>
        <el-menu-item index="/">
          <span class="menu-item-inner"><AppEmoji name="home" size="sm" decorative />首页</span>
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

        <!-- 系统管理：多级菜单（仅管理员），默认不展开 -->
        <el-sub-menu v-if="auth.isAdmin" index="sys-root">
          <template #title>
            <span class="menu-item-inner"><AppEmoji name="systemMgmt" size="sm" decorative />系统管理</span>
          </template>
          <el-sub-menu index="sys-users-tree">
            <template #title>
              <span class="submenu-title"><AppEmoji name="users" size="sm" decorative />用户管理</span>
            </template>
            <el-menu-item index="/system/users">
              <span class="menu-item-inner"><AppEmoji name="userInfo" size="sm" decorative />用户信息</span>
            </el-menu-item>
            <el-menu-item index="/system/roles">
              <span class="menu-item-inner"><AppEmoji name="rolePerm" size="sm" decorative />角色权限</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="sys-basic">
            <template #title>
              <span class="submenu-title"><AppEmoji name="basicInfo" size="sm" decorative />基础信息</span>
            </template>
            <el-menu-item index="/system/enterprise">
              <span class="menu-item-inner"><AppEmoji name="enterprise" size="sm" decorative />企业信息</span>
            </el-menu-item>
            <el-menu-item index="/system/course">
              <span class="menu-item-inner"><AppEmoji name="course" size="sm" decorative />课程信息</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="sys-settings">
            <template #title>
              <span class="submenu-title"><AppEmoji name="settingsCenter" size="sm" decorative />设置中心</span>
            </template>
            <el-menu-item index="/system/document-design">
              <span class="menu-item-inner"><AppEmoji name="documentDesign" size="sm" decorative />单据设计</span>
            </el-menu-item>
            <el-menu-item index="/system/print-settings">
              <span class="menu-item-inner"><AppEmoji name="printSettings" size="sm" decorative />打印设置</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="sys-supervision">
            <template #title>
              <span class="submenu-title"><AppEmoji name="supervision" size="sm" decorative />监管服务</span>
            </template>
            <el-menu-item index="/system/online-users">
              <span class="menu-item-inner"><AppEmoji name="onlineUsers" size="sm" decorative />在线用户</span>
            </el-menu-item>
            <el-menu-item index="/system/logs">
              <span class="menu-item-inner"><AppEmoji name="logMgmt" size="sm" decorative />日志管理</span>
            </el-menu-item>
          </el-sub-menu>
        </el-sub-menu>

        <el-menu-item v-if="auth.isAdmin" index="/bi">
          <span class="menu-item-inner"><AppEmoji name="biCenter" size="sm" decorative />数智BI中心</span>
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
.submenu-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
</style>
