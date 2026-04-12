<template>
  <div class="wrap">
    <div class="bg-grid" aria-hidden="true" />
    <div class="glow glow-a" aria-hidden="true" />
    <div class="glow glow-b" aria-hidden="true" />
    <el-card class="card" shadow="always">
      <template #header>
        <div class="card-title">
          <AppEmoji name="login" size="lg" decorative />
          <span>考试系统登录</span>
        </div>
      </template>
      <el-form @submit.prevent="onSubmit" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" autocomplete="current-password" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="btn-login">
          <AppEmoji name="login" size="sm" decorative />登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const username = ref("");
const password = ref("");
const loading = ref(false);

async function onSubmit() {
  loading.value = true;
  try {
    await auth.login(username.value, password.value);
    const redir = (route.query.redirect as string) || "/";
    await router.replace(redir);
  } catch {
    ElMessage.error("登录失败，请检查账号密码或稍后重试");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.wrap {
  position: relative;
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: linear-gradient(145deg, #070f1c 0%, #0b1f36 42%, #0a2844 100%);
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(0, 200, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 200, 255, 0.07) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse at center, black 0%, transparent 72%);
  pointer-events: none;
}

.glow {
  position: absolute;
  width: 520px;
  height: 520px;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.35;
  pointer-events: none;
}
.glow-a {
  left: -120px;
  top: 10%;
  background: radial-gradient(circle, #00c8ff 0%, transparent 70%);
}
.glow-b {
  right: -160px;
  bottom: 0;
  background: radial-gradient(circle, #6b5cff 0%, transparent 70%);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card {
  position: relative;
  z-index: 1;
  width: 420px;
  border: 1px solid rgba(0, 210, 255, 0.28);
  background: rgba(8, 18, 34, 0.82);
  backdrop-filter: blur(10px);
  box-shadow: 0 0 0 1px rgba(0, 200, 255, 0.08), 0 24px 48px rgba(0, 0, 0, 0.45);
}

:deep(.el-card__header) {
  color: #7ee8ff;
  font-weight: 600;
  letter-spacing: 0.04em;
  border-bottom: 1px solid rgba(0, 200, 255, 0.22);
  background: linear-gradient(90deg, rgba(0, 200, 255, 0.08), transparent);
}

:deep(.el-form-item__label) {
  color: #a8d8ee;
}

:deep(.el-input__wrapper) {
  background-color: rgba(6, 16, 32, 0.65);
  box-shadow: 0 0 0 1px rgba(0, 200, 255, 0.18) inset;
}

:deep(.el-input__inner) {
  color: #e8f4ff;
}

.btn-login {
  width: 100%;
  margin-top: 4px;
  background: linear-gradient(90deg, #0ea5e9, #6366f1);
  border: none;
}
.btn-login:hover {
  filter: brightness(1.06);
}
</style>
