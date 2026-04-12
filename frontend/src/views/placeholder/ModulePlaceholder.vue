<template>
  <el-card class="ph-card">
    <template #header>
      <span class="ph-title">{{ pageTitle }}</span>
    </template>
    <p class="ph-tip">功能建设中，敬请期待。</p>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const pageTitle = computed(() => (route.meta.title as string) || "页面");
</script>

<style scoped>
.ph-title {
  font-weight: 600;
  color: #1e293b;
}
.ph-tip {
  margin: 0;
  color: #64748b;
  line-height: 1.6;
}
.ph-card {
  min-height: 200px;
}
</style>
