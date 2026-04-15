<template>
  <div class="fill-height design-wrap">
    <el-card class="page-list-card">
      <template #header>
        <div class="hdr">
          <span>模板设计中心 — {{ headerTitle }}</span>
          <div class="hdr-actions">
            <el-button @click="goBack">返回列表</el-button>
            <el-button type="primary" :loading="saving" @click="saveLayout">保存版式</el-button>
            <el-button @click="previewPrint">预览打印</el-button>
          </div>
        </div>
      </template>
      <el-alert
        title="依据纸张大小设置页边距与字号；保存后供后期试卷打印接口或前端插件调用。"
        type="info"
        :closable="false"
        class="mb12"
      />
      <el-form v-if="layout" label-width="140px" class="design-form">
        <el-form-item label="纸张规格">
          <el-select v-model="paperFormat" style="width: 200px" @change="onPaperFormatChange">
            <el-option label="A4" value="A4" />
            <el-option label="A3" value="A3" />
            <el-option label="B5" value="B5" />
            <el-option label="自定义" value="CUSTOM" />
          </el-select>
        </el-form-item>
        <el-form-item label="宽×高(mm)">
          <el-input-number v-model="paperW" :min="50" :max="500" /> ×
          <el-input-number v-model="paperH" :min="50" :max="800" />
        </el-form-item>
        <el-form-item label="页边距(mm)">
          上
          <el-input-number v-model="marginTop" :min="0" :max="80" class="mrg" />
          右
          <el-input-number v-model="marginRight" :min="0" :max="80" class="mrg" />
          下
          <el-input-number v-model="marginBottom" :min="0" :max="80" class="mrg" />
          左
          <el-input-number v-model="marginLeft" :min="0" :max="80" class="mrg" />
        </el-form-item>
        <el-form-item label="页眉">
          <el-switch v-model="headerShow" />
        </el-form-item>
        <template v-if="headerShow">
          <el-form-item label="标题占位">
            <el-input v-model="headerTitleTpl" placeholder="支持 {{paper_title}}" />
          </el-form-item>
          <el-form-item label="页眉字号(pt)">
            <el-input-number v-model="headerFont" :min="8" :max="36" />
          </el-form-item>
          <el-form-item label="对齐">
            <el-radio-group v-model="headerAlign">
              <el-radio-button label="left">左</el-radio-button>
              <el-radio-button label="center">中</el-radio-button>
              <el-radio-button label="right">右</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </template>
        <el-form-item label="正文题号区字号(pt)">
          <el-input-number v-model="qFont" :min="8" :max="24" />
        </el-form-item>
        <el-form-item label="行距">
          <el-input-number v-model="qLh" :min="1" :max="3" :step="0.1" />
        </el-form-item>
        <el-form-item label="页脚">
          <el-switch v-model="footerShow" />
        </el-form-item>
        <el-form-item v-if="footerShow" label="页脚文字模板">
          <el-input v-model="footerTpl" placeholder="如第 {{page}}页 / 共 {{pages}} 页" />
        </el-form-item>
        <el-form-item v-if="footerShow" label="页脚字号(pt)">
          <el-input-number v-model="footerFont" :min="6" :max="18" />
        </el-form-item>
      </el-form>
      <div v-if="layout" class="preview-box">
        <div class="preview-label">版式预览（示意）</div>
        <div class="preview-page" :style="previewStyle">
          <div v-if="headerShow" class="pv-h">{{ previewTitle }}</div>
          <div class="pv-body">（题目区域）</div>
          <div v-if="footerShow" class="pv-f">页脚示意</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { getPrintTemplate, updatePrintTemplate } from "@/api/print_templates";
import { buildPaperPrintHtml, openPaperPrint } from "@/plugins/paperPrint";

const route = useRoute();
const router = useRouter();

const templateId = computed(() => Number(route.params.id));
const headerTitle = ref("");
const saving = ref(false);
const layout = ref<Record<string, unknown> | null>(null);
const tplMeta = ref<{ template_no?: string; course_name?: string }>({});

const paperFormat = ref("A4");
const paperW = ref(210);
const paperH = ref(297);
const marginTop = ref(15);
const marginRight = ref(15);
const marginBottom = ref(15);
const marginLeft = ref(15);
const headerShow = ref(true);
const headerTitleTpl = ref("{{paper_title}}");
const headerFont = ref(14);
const headerAlign = ref("center");
const qFont = ref(11);
const qLh = ref(1.6);
const footerShow = ref(true);
const footerTpl = ref("第 {{page}}页 / 共 {{pages}} 页");
const footerFont = ref(9);

const PRESET: Record<string, [number, number]> = {
  A4: [210, 297],
  A3: [297, 420],
  B5: [176, 250],
  CUSTOM: [210, 297],
};

function onPaperFormatChange() {
  const p = PRESET[paperFormat.value] || PRESET.A4;
  paperW.value = p[0];
  paperH.value = p[1];
}

function readFromLayout(L: Record<string, unknown>) {
  const paper = (L.paper || {}) as Record<string, unknown>;
  const fmtRaw = ((paper.format as string) || "A4").toUpperCase();
  paperFormat.value = fmtRaw in PRESET ? fmtRaw : "A4";
  const pr = PRESET[paperFormat.value] || PRESET.A4;
  paperW.value = Number(paper.widthMm) || pr[0];
  paperH.value = Number(paper.heightMm) || pr[1];
  const m = (L.marginMm || {}) as Record<string, number>;
  marginTop.value = Number(m.top) >= 0 ? Number(m.top) : 15;
  marginRight.value = Number(m.right) >= 0 ? Number(m.right) : 15;
  marginBottom.value = Number(m.bottom) >= 0 ? Number(m.bottom) : 15;
  marginLeft.value = Number(m.left) >= 0 ? Number(m.left) : 15;
  const h = (L.header || {}) as Record<string, unknown>;
  headerShow.value = h.show !== false;
  headerTitleTpl.value = (h.titleTemplate as string) || "{{paper_title}}";
  headerFont.value = Number(h.fontPt) > 0 ? Number(h.fontPt) : 14;
  headerAlign.value = (h.align as string) || "center";
  const q = (L.question || {}) as Record<string, unknown>;
  qFont.value = Number(q.fontPt) > 0 ? Number(q.fontPt) : 11;
  qLh.value = Number(q.lineHeight) > 0 ? Number(q.lineHeight) : 1.6;
  const f = (L.footer || {}) as Record<string, unknown>;
  footerShow.value = f.show !== false;
  footerTpl.value = (f.textTemplate as string) || "第 {{page}}页 / 共 {{pages}} 页";
  footerFont.value = Number(f.fontPt) > 0 ? Number(f.fontPt) : 9;
}

function buildLayoutJson(): Record<string, unknown> {
  return {
    paper: {
      format: paperFormat.value,
      widthMm: paperW.value,
      heightMm: paperH.value,
      portrait: true,
    },
    marginMm: {
      top: marginTop.value,
      right: marginRight.value,
      bottom: marginBottom.value,
      left: marginLeft.value,
    },
    header: {
      show: headerShow.value,
      titleTemplate: headerTitleTpl.value,
      fontPt: headerFont.value,
      align: headerAlign.value,
    },
    question: { fontPt: qFont.value, lineHeight: qLh.value },
    footer: {
      show: footerShow.value,
      textTemplate: footerTpl.value,
      fontPt: footerFont.value,
    },
  };
}

const previewStyle = computed(() => {
  const scale = 0.35;
  return {
    width: `${paperW.value * scale}px`,
    minHeight: `${paperH.value * scale}px`,
    padding: `${marginTop.value * scale}px ${marginRight.value * scale}px ${marginBottom.value * scale}px ${marginLeft.value * scale}px`,
  };
});

const previewTitle = computed(() => {
  const t = headerTitleTpl.value.replace(/\{\{\s*paper_title\s*\}\}/gi, "试卷标题示例");
  return t;
});

async function load() {
  try {
    const { data } = await getPrintTemplate(templateId.value);
    tplMeta.value = { template_no: data.template_no, course_name: data.course_name };
    headerTitle.value = `${data.template_no || ""} / ${data.course_name || ""}`;
    layout.value = data.layout_json || {};
    readFromLayout(layout.value as Record<string, unknown>);
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载模板失败"));
  }
}

async function saveLayout() {
  saving.value = true;
  try {
    const L = buildLayoutJson();
    await updatePrintTemplate(templateId.value, { layout_json: L, paper_format: paperFormat.value });
    layout.value = L;
    ElMessage.success("版式已保存");
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  } finally {
    saving.value = false;
  }
}

function previewPrint() {
  const L = buildLayoutJson();
  const html = buildPaperPrintHtml(L, {
    paperTitle: tplMeta.value.template_no || "试卷打印预览",
    questionBlocks: ["一、单选题（示例）", "1. 示例题干 __________"],
  });
  openPaperPrint(html);
}

function goBack() {
  router.push({ name: "system-print-settings" });
}

onMounted(() => {
  if (!Number.isFinite(templateId.value) || templateId.value < 1) {
    ElMessage.error("无效的模板");
    router.push({ name: "system-print-settings" });
    return;
  }
  void load();
});
</script>

<style scoped>
.design-wrap {
  padding: 0;
}
.hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.hdr-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.mb12 {
  margin-bottom: 12px;
}
.design-form {
  max-width: 720px;
}
.mrg {
  width: 100px;
  margin-right: 8px;
}
.preview-box {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.preview-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}
.preview-page {
  border: 1px dashed #999;
  background: #fafafa;
  box-sizing: border-box;
}
.pv-h {
  text-align: center;
  font-weight: 600;
  margin-bottom: 8px;
}
.pv-body {
  font-size: 12px;
  color: #666;
  min-height: 80px;
}
.pv-f {
  text-align: center;
  font-size: 11px;
  color: #999;
  margin-top: 12px;
}
</style>
