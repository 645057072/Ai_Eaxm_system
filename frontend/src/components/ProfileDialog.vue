<template>
  <el-dialog :model-value="modelValue" title="个人信息" width="520px" destroy-on-close @update:model-value="emit('update:modelValue', $event)">
    <el-tabs>
      <el-tab-pane label="安全设置">
        <el-form label-width="100px" class="pwd-form">
          <el-form-item label="原密码">
            <el-input v-model="pwd.old" type="password" show-password autocomplete="off" />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="pwd.n" type="password" show-password autocomplete="off" />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="pwd.n2" type="password" show-password autocomplete="off" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="savePwd">保存密码</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="显示风格">
        <p class="theme-tip">预置五套界面主色与侧栏渐变，突出科技与数智感，选择后立即生效。</p>
        <div class="theme-grid">
          <button
            v-for="opt in themeOptions"
            :key="opt.id"
            type="button"
            class="theme-card"
            :class="{ active: currentTheme === opt.id }"
            @click="pickTheme(opt.id)"
          >
            <span class="theme-swatch" :style="{ background: opt.swatch }" />
            <span class="theme-name">{{ opt.title }}</span>
            <span class="theme-desc">{{ opt.desc }}</span>
          </button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { changeMyPassword } from "@/api/auth";
import { applyUiTheme, getStoredUiTheme, type UiThemeId, UI_THEME_IDS } from "@/utils/uiTheme";

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ (e: "update:modelValue", v: boolean): void }>();

const pwd = reactive({ old: "", n: "", n2: "" });
const currentTheme = ref<UiThemeId>(getStoredUiTheme());

const themeOptions: { id: UiThemeId; title: string; desc: string; swatch: string }[] = [
  { id: "nebula", title: "星云智链", desc: "靛紫科技、智慧连接", swatch: "linear-gradient(135deg,#6366f1,#8b5cf6)" },
  { id: "aurora", title: "极光智域", desc: "青绿极光、清透智感", swatch: "linear-gradient(135deg,#0d9488,#06b6d4)" },
  { id: "deepblue", title: "深潜蓝图", desc: "深蓝专业、理性科技", swatch: "linear-gradient(135deg,#1d4ed8,#2563eb)" },
  { id: "amber", title: "琥珀慧核", desc: "琥珀暖金、沉稳智慧", swatch: "linear-gradient(135deg,#d97706,#f59e0b)" },
  { id: "jade", title: "青玉数智", desc: "翡翠智慧、生长型数据", swatch: "linear-gradient(135deg,#059669,#10b981)" },
];

watch(
  () => props.modelValue,
  (v) => {
    if (v) currentTheme.value = getStoredUiTheme();
  },
);

function pickTheme(id: UiThemeId) {
  if (!UI_THEME_IDS.includes(id)) return;
  applyUiTheme(id);
  currentTheme.value = id;
  ElMessage.success("已切换显示风格");
}

async function savePwd() {
  if (!pwd.old || !pwd.n) {
    ElMessage.warning("请填写原密码与新密码");
    return;
  }
  if (pwd.n.length < 6) {
    ElMessage.warning("新密码至少 6 位");
    return;
  }
  if (pwd.n !== pwd.n2) {
    ElMessage.warning("两次新密码不一致");
    return;
  }
  try {
    await changeMyPassword(pwd.old, pwd.n);
    ElMessage.success("密码已更新");
    pwd.old = "";
    pwd.n = "";
    pwd.n2 = "";
    emit("update:modelValue", false);
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "修改失败"));
  }
}
</script>

<style scoped>
.theme-tip {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 14px;
  line-height: 1.5;
}
.theme-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.theme-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fafbfc;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.theme-card:hover {
  border-color: #cbd5e1;
}
.theme-card.active {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 1px var(--el-color-primary);
}
.theme-swatch {
  width: 100%;
  height: 36px;
  border-radius: 6px;
}
.theme-name {
  font-weight: 600;
  color: #334155;
  font-size: 14px;
}
.theme-desc {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.35;
}
.pwd-form {
  padding-top: 8px;
}
</style>
