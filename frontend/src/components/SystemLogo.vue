<template>
  <!-- 品牌标识：立体 ZK 字标 + AI 神经网络环 + 玻璃拟态底板（登录/侧栏/顶栏三态） -->
  <div class="system-logo" :class="`variant-${variant}`" role="img" :aria-label="ariaLabel">
    <svg class="mark" viewBox="0 0 72 72" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <linearGradient :id="faceGrad" x1="8" y1="10" x2="62" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0%" :stop-color="g1" />
          <stop offset="42%" :stop-color="g2" />
          <stop offset="100%" :stop-color="g3" />
        </linearGradient>
        <linearGradient :id="rimGrad" x1="36" y1="6" x2="36" y2="66" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#ffffff" stop-opacity="0.55" />
          <stop offset="40%" :stop-color="g1" stop-opacity="0.35" />
          <stop offset="100%" :stop-color="g3" stop-opacity="0.5" />
        </linearGradient>
        <radialGradient :id="coreGlow" cx="36" cy="34" r="22" gradientUnits="userSpaceOnUse">
          <stop offset="0%" :stop-color="g1" stop-opacity="0.45" />
          <stop offset="70%" :stop-color="g2" stop-opacity="0.12" />
          <stop offset="100%" stop-color="transparent" />
        </radialGradient>
        <filter :id="softShadow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="1.8" stdDeviation="1.2" flood-color="#0f172a" flood-opacity="0.35" />
        </filter>
        <filter :id="innerGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="0.6" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <!-- 圆角超椭圆底板 + 内光 -->
      <rect        x="4"
        y="4"
        width="64"
        height="64"
        rx="18"
        fill="rgba(15,23,42,0.2)"
        :stroke="`url(#${rimGrad})`"
        stroke-width="1.35"
      />
      <rect x="7" y="7" width="58" height="58" rx="15" :fill="`url(#${coreGlow})`" />

      <!-- AI 轨道：虚线环 + 节点 -->
      <g fill="none" stroke-linecap="round" opacity="0.92">
        <ellipse
          cx="36"
          cy="36"
          rx="26"
          ry="12"
          :stroke="g1"
          stroke-width="0.85"
          stroke-dasharray="3 4"
          transform="rotate(-18 36 36)"
        />
        <ellipse
          cx="36"
          cy="36"
          rx="26"
          ry="12"
          :stroke="g2"
          stroke-width="0.75"
          stroke-dasharray="2 5"
          transform="rotate(38 36 36)"
        />
        <path d="M22 48 Q36 56 50 46" :stroke="g3" stroke-width="0.9" opacity="0.85" />
        <circle cx="22" cy="26" r="2.1" :fill="chipFill" :stroke="g1" stroke-width="0.6" />
        <circle cx="50" cy="28" r="2.1" :fill="chipFill" :stroke="g2" stroke-width="0.6" />
        <circle cx="36" cy="20" r="2.35" :fill="chipFill" :stroke="g3" stroke-width="0.65" />
        <circle cx="30" cy="50" r="1.65" :fill="chipFill" :stroke="g1" stroke-width="0.55" />
        <circle cx="46" cy="48" r="1.65" :fill="chipFill" :stroke="g2" stroke-width="0.55" />
      </g>

      <!-- ZK 立体：底层挤出 -->
      <g opacity="0.88" transform="translate(2.4, 2.55)">
        <path
          :fill="extrudeFill"
          d="M14.2 24.5L32.6 24.5L32.6 28.2L16.8 40.2L32.6 40.2L32.6 43.8L14.2 43.8L14.2 40.2L28.8 28.2L14.2 28.2z
 M36.2 24.5H40.4V34.2L56.2 24.5H60.2L46.2 35L59.8 43.8H55.4L40.4 36.2V43.8H36.2V24.5z"
        />
      </g>
      <!-- ZK 面层高光 -->
      <g :filter="`url(#${softShadow})`">
        <path
          :fill="`url(#${faceGrad})`"
          stroke="rgba(255,255,255,0.28)"
          stroke-width="0.4"
          d="M14.2 24.5L32.6 24.5L32.6 28.2L16.8 40.2L32.6 40.2L32.6 43.8L14.2 43.8L14.2 40.2L28.8 28.2L14.2 28.2z
             M36.2 24.5H40.4V34.2L56.2 24.5H60.2L46.2 35L59.8 43.8H55.4L40.4 36.2V43.8H36.2V24.5z"
        />
      </g>
      <path
        fill="rgba(255,255,255,0.42)"
        opacity="0.55"
        d="M15 24.5H31.5V25.9H15z M36.4 24.5H40.2V25.9H36.4z"
      />

      <!-- AI 角标 -->
      <g :filter="`url(#${innerGlow})`">
        <path
          d="M52 10L62 10L62 20Q57 22 52 18z"
          :fill="badgeFill"
          :stroke="g1"
          stroke-width="0.5"
          opacity="0.95"
        />
        <text x="54.5" y="17.5" font-size="6.5" font-weight="800" fill="white" font-family="system-ui,sans-serif">
          AI
        </text>
      </g>
    </svg>
    <div v-if="showTitle" class="titles">
      <span class="name cn">{{ displayTitleCn }}</span>
      <span class="name en">{{ displayTitleEn }}</span>
      <span v-if="subtitle" class="sub">{{ subtitle }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, useId } from "vue";

const props = withDefaults(
  defineProps<{
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
const faceGrad = computed(() => `zk-face-${uid}`);
const rimGrad = computed(() => `zk-rim-${uid}`);
const coreGlow = computed(() => `zk-core-${uid}`);
const softShadow = computed(() => `zk-sh-${uid}`);
const innerGlow = computed(() => `zk-in-${uid}`);

const ariaLabel = "Ai 智库 ZK 考试系统";

const defaultTitleCn = "Ai 智库（ZK）考试系统";
const defaultTitleEn = "AI Knowledge Base (ZK) Exam System";

const displayTitleCn = computed(() => props.titleText ?? defaultTitleCn);
const displayTitleEn = computed(() => defaultTitleEn);

const lightBg = computed(() => props.variant === "sidebar" || props.variant === "header");

const g1 = computed(() => (lightBg.value ? "#0369a1" : "#38bdf8"));
const g2 = computed(() => (lightBg.value ? "#4338ca" : "#818cf8"));
const g3 = computed(() => (lightBg.value ? "#6d28d9" : "#c084fc"));

const extrudeFill = computed(() => (lightBg.value ? "#1e1b4b" : "#0f172a"));
const chipFill = computed(() => (lightBg.value ? "#f8fafc" : "#e2e8f0"));
const badgeFill = computed(() => (lightBg.value ? "#0ea5e9" : "#0284c7"));
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
  width: 80px;
  height: 80px;
  filter: drop-shadow(0 4px 12px rgba(15, 23, 42, 0.45)) drop-shadow(0 0 24px rgba(56, 189, 248, 0.35));
}

.variant-sidebar .mark {
  width: 42px;
  height: 42px;
  filter: drop-shadow(0 2px 6px rgba(15, 23, 42, 0.12));
}

.variant-header .mark {
  width: 34px;
  height: 34px;
  filter: drop-shadow(0 1px 4px rgba(15, 23, 42, 0.1));
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
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  line-height: 1.3;
  background: linear-gradient(115deg, #7dd3fc 0%, #a5b4fc 38%, #e879f9 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.08);
}

.variant-login .name.en {
  font-size: 0.92rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: rgba(226, 232, 240, 0.9);
  background: none;
  -webkit-background-clip: initial;
  background-clip: initial;
  text-shadow: none;
}

.variant-login .sub {
  font-size: 0.82rem;
  color: rgba(186, 230, 253, 0.9);
  letter-spacing: 0.08em;
}

.variant-sidebar .titles,
.variant-header .titles {
  gap: 0;
}

.variant-sidebar .name,
.variant-header .name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}

.variant-sidebar .name.cn {
  font-size: 0.9rem;
  font-weight: 800;
  background: linear-gradient(90deg, #0f172a 0%, #334155 55%, #4f46e5 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  letter-spacing: 0.03em;
  line-height: 1.25;
}

.variant-sidebar .name.en {
  font-size: 0.72rem;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.06em;
  line-height: 1.2;
}

.variant-sidebar .sub {
  font-size: 0.72rem;
  color: #64748b;
}

.variant-header .name.cn {
  font-size: 0.88rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  background: linear-gradient(90deg, #0f172a, #4338ca);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  line-height: 1.2;
}

.variant-header .name.en {
  font-size: 0.7rem;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.06em;
  line-height: 1.15;
}

.variant-header {
  gap: 8px;
}
</style>
