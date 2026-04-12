<script setup lang="ts">
import { computed } from "vue";
import type { SystemEmojiKey } from "@/assets/emoji/systemEmoji";
import { getSystemEmoji } from "@/assets/emoji/systemEmoji";

const props = withDefaults(
  defineProps<{
    /** 资源键，对应 systemEmoji 中的条目 */
    name: SystemEmojiKey;
    /** 尺寸 */
    size?: "sm" | "md" | "lg";
    /**
     * 无障碍：有意义的独立图标时传入简短说明；与文案重复的装饰性图标可设 decorative
     */
    label?: string;
    /** 为 true 时对读屏隐藏（与相邻文字语义重复时） */
    decorative?: boolean;
  }>(),
  {
    size: "md",
    decorative: false,
  },
);

const char = computed(() => getSystemEmoji(props.name));

const attrs = computed(() => {
  if (props.decorative) {
    return { "aria-hidden": "true" as const };
  }
  return {
    role: "img" as const,
    "aria-label": props.label ?? char.value,
  };
});

const klass = computed(() => ["app-emoji", `app-emoji--${props.size}`]);
</script>

<template>
  <span :class="klass" v-bind="attrs">{{ char }}</span>
</template>

<style scoped>
.app-emoji {
  display: inline-block;
  line-height: 1;
  vertical-align: -0.12em;
  font-style: normal;
  user-select: none;
}
.app-emoji--sm {
  font-size: 0.95em;
}
.app-emoji--md {
  font-size: 1.12em;
}
.app-emoji--lg {
  font-size: 1.4em;
}
</style>
