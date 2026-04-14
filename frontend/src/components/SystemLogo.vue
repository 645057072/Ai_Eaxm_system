<template>
  <!-- 系统品牌标识：ZK 立体字标 + AI 神经节点（原创矢量），用于登录与主导航 -->
  <div class="system-logo" :class="`variant-${variant}`" role="img" :aria-label="ariaLabel">
    <svg class="mark" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <linearGradient :id="gradId" x1="10" y1="12" x2="54" y2="52" gradientUnits="userSpaceOnUse">
          <stop offset="0%" :stop-color="stop1" />
          <stop offset="45%" :stop-color="stop2" />
          <stop offset="100%" :stop-color="stop3" />
        </linearGradient>
        <linearGradient :id="topHiId" gradientUnits="userSpaceOnUse" x1="11" y1="16" x2="11" y2="19">
          <stop offset="0%" stop-color="#f0f9ff" />
          <stop offset="100%" :stop-color="stop1" stop-opacity="0" />
        </linearGradient>
        <filter :id="filterId" x="-25%" y="-25%" width="150%" height="150%">
          <feGaussianBlur in="SourceAlpha" stdDeviation="0.7" result="b" />
          <feOffset dx="0" dy="0.45" in="b" result="o" />
          <feMerge>
            <feMergeNode in="o" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <rect
        x="5"
        y="5"
        width="54"
        height="54"
        rx="14"
        fill="rgba(15,23,42,0.32)"
        :stroke="`url(#${gradId})`"
        stroke-width="2"
      />
      <g opacity="0.9" transform="translate(2.05,2.2)">
        <path
          :fill="extrusionFill"
          d="M11.5 16.2L27.3 16.2L27.3 19.3L14 29.4L27.3 29.4L27.3 32.5L11.5 32.5L11.5 29.4L24.2 19.3L11.5 19.3z M30.2 16.2H33.8V24.5L47.5 16.2H50.8L38.5 25.2L50.5 32.5H46.8L33.8 26.5V32.5H30.2V16.2z"
        />
      </g>
      <g :filter="`url(#${filterId})`">
        <path
          :fill="`url(#${gradId})`"
          stroke="rgba(255,255,255,0.22)"
          stroke-width="0.35"
          d="M11.5 16.2L27.3 16.2L27.3 19.3L14 29.4L27.3 29.4L27.3 32.5L11.5 32.5L11.5 29.4L24.2 19.3L11.5 19.3z
             M30.2 16.2H33.8V24.5L47.5 16.2H50.8L38.5 25.2L50.5 32.5H46.8L33.8 26.5V32.5H30.2V16.2z"
        />
      </g>
      <path :fill="`url(#${topHiId})`" opacity="0.55" d="M12 16.2H26.8V17.35H12z M30.4 16.2H33.6V17.35H30.4z" />
      <g stroke-linecap="round">
        <path
          d="M27.6 22C30 20.6 34 20.6 36.4 22"
          fill="none"
          stroke="#67e8f9"
          stroke-width="1.05"
          opacity="0.9"
        />
        <path
          d="M32.4 25.2C33.8 27.8 37 29.5 40.2 30.5"
          fill="none"
          stroke="#c4b5fd"
          stroke-width="0.95"
          opacity="0.82"
        />
        <circle cx="27.5" cy="22.1" r="2" fill="#e0f2fe" :stroke="stop1" stroke-width="0.85" />
        <circle cx="36.5" cy="22.1" r="2" fill="#e0e7ff" :stroke="stop2" stroke-width="0.85" />
        <circle cx="32" cy="26.6" r="2.2" fill="#fae8ff" :stroke="stop3" stroke-width="0.85" />
        <circle cx="23.6" cy="30.4" r="1.5" fill="#cffafe" :stroke="stop1" stroke-width="0.7" />
        <circle cx="40.4" cy="31" r="1.5" fill="#ede9fe" :stroke="stop3" stroke-width="0.7" />
      </g>
      <path
        d="M13 50.5h5.5m7 0h5.5m7 0h5.5m7 0h5.5"
        :stroke="tickColor"
        stroke-width="1.35"
        stroke-linecap="round"
        opacity="0.65"
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
const topHiId = computed(() => `zk-top-${uid}`);
const filterId = computed(() => `zk-soft-${uid}`);

const ariaLabel = "Ai 智库 ZK 考试系统";

const defaultTitle = "Ai 智库（ZK）考试系统";

const displayTitle = computed(() => props.titleText ?? defaultTitle);

const lightBg = computed(() => props.variant === "sidebar" || props.variant === "header");

const stop1 = computed(() => (lightBg.value ? "#0284c7" : "#38bdf8"));
const stop2 = computed(() => (lightBg.value ? "#4f46e5" : "#6366f1"));
const stop3 = computed(() => (lightBg.value ? "#7c3aed" : "#a78bfa"));

const tickColor = computed(() => (lightBg.value ? "#64748b" : "#94a3b8"));

/** 立体暗层填充（与主渐变同色系、压暗） */
const extrusionFill = computed(() => (lightBg.value ? "#312e81" : "#1e1b4b"));
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
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.35)) drop-shadow(0 0 16px rgba(56, 189, 248, 0.42));
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
