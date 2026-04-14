<template>
  <!-- 系统品牌标识：原创 SVG（知识节点网络 + 芯片轮廓），用于登录与主导航 -->
  <div class="system-logo" :class="`variant-${variant}`" role="img" :aria-label="ariaLabel">
    <svg class="mark" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <linearGradient :id="gradId" x1="8" y1="8" x2="56" y2="56" gradientUnits="userSpaceOnUse">
          <stop offset="0%" :stop-color="stop1" />
          <stop offset="55%" :stop-color="stop2" />
          <stop offset="100%" :stop-color="stop3" />
        </linearGradient>
      </defs>
      <rect
        x="6"
        y="6"
        width="52"
        height="52"
        rx="14"
        fill="none"
        :stroke="`url(#${gradId})`"
        stroke-width="2.2"
      />
      <circle cx="22" cy="26" r="3.5" :fill="`url(#${gradId})`" />
      <circle cx="42" cy="26" r="3.5" :fill="`url(#${gradId})`" />
      <circle cx="32" cy="40" r="4.2" :fill="`url(#${gradId})`" opacity="0.95" />
      <path
        d="M22 26 L32 40 L42 26"
        fill="none"
        :stroke="`url(#${gradId})`"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path
        d="M14 50h6m6 0h6m6 0h6m6 0h6"
        :stroke="tickColor"
        stroke-width="1.5"
        stroke-linecap="round"
        opacity="0.72"
      />
    </svg>
    <div v-if="showTitle" class="titles">
      <span class="name">{{ displayTitle }}</span>
      <span v-if="subtitle" class="sub">{{ subtitle }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, useId } from "vue";

const props = withDefaults(
  defineProps<{
    /** login：登录页大图标；sidebar：侧栏；header：顶栏紧凑 */
    variant?: "login" | "sidebar" | "header";
    showTitle?: boolean;
    titleText?: string;
    subtitle?: string;
  }>(),
  {
    variant: "sidebar",
    showTitle: true,
    titleText: undefined,
    subtitle: "",
  },
);

const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");
const gradId = computed(() => `zk-grad-${uid}`);

const ariaLabel = "Ai 智库 ZK 考试系统";

const defaultTitle = "Ai 智库（ZK）考试系统";

const displayTitle = computed(() => props.titleText ?? defaultTitle);

const lightBg = computed(() => props.variant === "sidebar" || props.variant === "header");

const stop1 = computed(() => (lightBg.value ? "#0284c7" : "#38bdf8"));
const stop2 = computed(() => (lightBg.value ? "#4f46e5" : "#6366f1"));
const stop3 = computed(() => (lightBg.value ? "#7c3aed" : "#a78bfa"));

const tickColor = computed(() => (lightBg.value ? "#64748b" : "#94a3b8"));
</script>

<style scoped>
.system-logo {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.mark {
  flex-shrink: 0;
  display: block;
}

.variant-login .mark {
  width: 72px;
  height: 72px;
  filter: drop-shadow(0 0 14px rgba(56, 189, 248, 0.38));
}

.variant-sidebar .mark {
  width: 40px;
  height: 40px;
}

.variant-header .mark {
  width: 32px;
  height: 32px;
}

.titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.variant-login .titles {
  text-align: left;
}

.variant-login .name {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  line-height: 1.35;
  background: linear-gradient(120deg, #7dd3fc 0%, #a5b4fc 45%, #c4b5fd 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.variant-login .sub {
  font-size: 0.8rem;
  color: rgba(148, 212, 255, 0.85);
  letter-spacing: 0.06em;
}

.variant-sidebar .titles,
.variant-header .titles {
  gap: 0;
}

.variant-sidebar .name {
  font-size: 0.88rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.02em;
  line-height: 1.3;
  max-width: 198px;
}

.variant-sidebar .sub {
  font-size: 0.72rem;
  color: #64748b;
}

.variant-header .name {
  font-size: 0.88rem;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: 0.02em;
}

.variant-header {
  gap: 8px;
}
</style>
