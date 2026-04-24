<template>
  <el-container class="layout">
    <el-aside width="256px" class="aside">
      <div class="brand">
        <SystemLogo variant="sidebar" :show-title="true" />
      </div>
      <el-menu :default-active="route.path" router>
        <el-menu-item index="/">
          <span class="menu-item-inner"><AppEmoji name="home" size="sm" decorative />首页</span>
        </el-menu-item>
        <el-sub-menu
          v-if="auth.canAny('menu.exam.qb_center', 'menu.exam.question_manage')"
          index="exam-qb-center"
        >
          <template #title>
            <span class="menu-item-inner"><AppEmoji name="questionBank" size="sm" decorative />题库中心</span>
          </template>
          <el-menu-item v-if="auth.can('menu.exam.question_manage')" index="/questions">
            <span class="menu-item-inner"><AppEmoji name="questionManage" size="sm" decorative />题库管理</span>
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu v-if="auth.canAny('menu.exam.paper_manage', 'menu.exam.paper_publish')" index="exam-paper-archive">
          <template #title>
            <span class="menu-item-inner"><AppEmoji name="papers" size="sm" decorative />试卷档案</span>
          </template>
          <el-menu-item v-if="auth.can('menu.exam.paper_manage')" index="/papers">
            <span class="menu-item-inner"><AppEmoji name="paperManage" size="sm" decorative />试卷管理</span>
          </el-menu-item>
          <el-menu-item v-if="auth.can('menu.exam.paper_publish')" index="/papers/publish">
            <span class="menu-item-inner"><AppEmoji name="publish" size="sm" decorative />场次发布</span>
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item v-if="auth.can('menu.exam.sessions')" index="/sessions">
          <span class="menu-item-inner"><AppEmoji name="sessions" size="sm" decorative />考试场次</span>
        </el-menu-item>
        <el-sub-menu
          v-if="
            auth.canAny(
              'menu.exam.available',
              'menu.exam.candidate_manage',
              'menu.exam.exam_services',
              'menu.exam.wrong_practice',
              'menu.exam.certificate',
            )
          "
          index="exam-manage"
        >
          <template #title>
            <span class="menu-item-inner"><AppEmoji name="availableExams" size="sm" decorative />考试管理</span>
          </template>
          <el-menu-item v-if="auth.can('menu.exam.available')" index="/exam/available">
            <span class="menu-item-inner"><AppEmoji name="availableExams" size="sm" decorative />在线考试</span>
          </el-menu-item>
          <el-menu-item v-if="auth.can('menu.exam.candidate_manage')" index="/exam/candidate-manage">
            <span class="menu-item-inner"><AppEmoji name="roleStudent" size="sm" decorative />考生管理</span>
          </el-menu-item>
          <el-menu-item v-if="auth.can('menu.exam.exam_services')" index="/exam/services">
            <span class="menu-item-inner"><AppEmoji name="sessions" size="sm" decorative />考试服务</span>
          </el-menu-item>
          <el-menu-item v-if="auth.can('menu.exam.certificate')" index="/exam/certificates">
            <span class="menu-item-inner"><AppEmoji name="certificate" size="sm" decorative />证书管理</span>
          </el-menu-item>
          <el-menu-item v-if="auth.can('menu.exam.wrong_practice')" index="/exam/wrong-practice">
            <span class="menu-item-inner"><AppEmoji name="questionBank" size="sm" decorative />错题练习</span>
          </el-menu-item>
        </el-sub-menu>

        <!-- 系统管理：按功能授权显示，默认不展开 -->
        <el-sub-menu
          v-if="
            auth.canAny(
              'menu.system.users',
              'menu.system.roles',
              'menu.system.enterprise',
              'menu.system.course',
              'menu.system.paper_level',
              'menu.system.document',
              'menu.system.print',
              'menu.system.online',
              'menu.system.logs',
            )
          "
          index="sys-root"
        >
          <template #title>
            <span class="menu-item-inner"><AppEmoji name="systemMgmt" size="sm" decorative />系统管理</span>
          </template>
          <el-sub-menu
            v-if="auth.canAny('menu.system.users', 'menu.system.roles')"
            index="sys-users-tree"
          >
            <template #title>
              <span class="submenu-title"><AppEmoji name="users" size="sm" decorative />用户管理</span>
            </template>
            <el-menu-item v-if="auth.can('menu.system.users')" index="/system/users">
              <span class="menu-item-inner"><AppEmoji name="userInfo" size="sm" decorative />用户信息</span>
            </el-menu-item>
            <el-menu-item v-if="auth.can('menu.system.roles')" index="/system/roles">
              <span class="menu-item-inner"><AppEmoji name="rolePerm" size="sm" decorative />角色权限</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu
            v-if="auth.canAny('menu.system.enterprise', 'menu.system.course', 'menu.system.paper_level', 'menu.system.student')"
            index="sys-basic"
          >
            <template #title>
              <span class="submenu-title"><AppEmoji name="basicInfo" size="sm" decorative />基础信息</span>
            </template>
            <el-menu-item v-if="auth.can('menu.system.enterprise')" index="/system/enterprise">
              <span class="menu-item-inner"><AppEmoji name="enterprise" size="sm" decorative />企业信息</span>
            </el-menu-item>
            <el-menu-item v-if="auth.can('menu.system.course')" index="/system/course">
              <span class="menu-item-inner"><AppEmoji name="course" size="sm" decorative />课程信息</span>
            </el-menu-item>
            <el-menu-item v-if="auth.can('menu.system.paper_level')" index="/system/paper-level">
              <span class="menu-item-inner"><AppEmoji name="paperLevel" size="sm" decorative />试卷等级</span>
            </el-menu-item>
            <el-menu-item v-if="auth.can('menu.system.student')" index="/system/students">
              <span class="menu-item-inner"><AppEmoji name="roleStudent" size="sm" decorative />学员管理</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu
            v-if="auth.canAny('menu.system.document', 'menu.system.print')"
            index="sys-settings"
          >
            <template #title>
              <span class="submenu-title"><AppEmoji name="settingsCenter" size="sm" decorative />设置中心</span>
            </template>
            <el-menu-item v-if="auth.can('menu.system.document')" index="/system/document-design">
              <span class="menu-item-inner"><AppEmoji name="documentDesign" size="sm" decorative />单据设计</span>
            </el-menu-item>
            <el-menu-item v-if="auth.can('menu.system.print')" index="/system/print-settings">
              <span class="menu-item-inner"><AppEmoji name="printSettings" size="sm" decorative />打印设置</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu
            v-if="auth.canAny('menu.system.online', 'menu.system.logs')"
            index="sys-supervision"
          >
            <template #title>
              <span class="submenu-title"><AppEmoji name="supervision" size="sm" decorative />监管服务</span>
            </template>
            <el-menu-item v-if="auth.can('menu.system.online')" index="/system/online-users">
              <span class="menu-item-inner"><AppEmoji name="onlineUsers" size="sm" decorative />在线用户</span>
            </el-menu-item>
            <el-menu-item v-if="auth.can('menu.system.logs')" index="/system/logs">
              <span class="menu-item-inner"><AppEmoji name="logMgmt" size="sm" decorative />日志管理</span>
            </el-menu-item>
          </el-sub-menu>
        </el-sub-menu>

        <el-menu-item v-if="auth.can('menu.bi')" index="/bi">
          <span class="menu-item-inner"><AppEmoji name="biCenter" size="sm" decorative />数智BI中心</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container class="layout-main-area">
      <el-header class="header">
        <div class="header-brand">
          <SystemLogo variant="header" :show-title="true" title-text="Ai 智库（ZK）" />
        </div>
        <div class="header-spacer" />
        <span class="who who-click" title="个人信息与显示风格" @click="profileOpen = true">
          <AppEmoji name="user" size="sm" decorative />
          {{ auth.me?.username }}（{{ auth.me?.role?.name }}）
          <span v-if="auth.me?.enterprise?.name" class="ent">· {{ auth.me.enterprise.name }}</span>
          <span v-else-if="auth.isAdmin" class="ent">· 全局管理</span>
        </span>
        <el-button type="danger" link @click="onLogout">
          <AppEmoji name="logout" size="sm" decorative />退出
        </el-button>
      </el-header>
      <el-main class="main">
        <router-view v-slot="{ Component, route: r }">
          <keep-alive include="RolePermissionPage">
            <component :is="Component" v-if="r.meta?.keepAlive" />
          </keep-alive>
          <component :is="Component" v-if="!r.meta?.keepAlive" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>
  <ProfileDialog v-model="profileOpen" />
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import ProfileDialog from "@/components/ProfileDialog.vue";
import SystemLogo from "@/components/SystemLogo.vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const profileOpen = ref(false);
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
.layout-main-area {
  flex: 1;
  min-width: 0;
  min-height: 0;
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
.header-brand {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.header-spacer {
  flex: 1;
  min-width: 8px;
}
.header {
  display: flex;
  align-items: center;
  justify-content: flex-start;
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
.who-click {
  cursor: pointer;
  user-select: none;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.15s;
}
.who-click:hover {
  background: rgba(15, 23, 42, 0.06);
}
.ent {
  color: #94a3b8;
  font-size: 13px;
}
.submenu-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.main {
  flex: 1;
  min-height: 0;
}
</style>
