<template>
  <!-- 数智大屏由独立 Flask 服务提供 HTML+ECharts，此处用同源 iframe 嵌入，避免重复实现图表 -->
  <div class="bi-screen-root">
    <iframe
      class="bi-screen-frame"
      title="数智BI可视化大屏"
      referrerpolicy="no-referrer-when-downgrade"
      :src="iframeSrc"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

/** 与 Flask /bi/screen 对齐：有企业则按企业树统计；超管无企业则由后端选默认顶级企业 */
const iframeSrc = computed(() => {
  const path = "/bi/screen";
  const eid = auth.me?.enterprise_id;
  if (eid != null && eid !== undefined) {
    return `${path}?enterprise_id=${encodeURIComponent(String(eid))}`;
  }
  return path;
});
</script>

<style scoped>
.bi-screen-root {
  /* 抵消 el-main 默认内边距，使大屏贴近可视区域 */
  margin: -20px;
  width: calc(100% + 40px);
  height: calc(100vh - 60px - 40px);
  min-height: 480px;
  background: #0a1628;
}
.bi-screen-frame {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}
</style>
