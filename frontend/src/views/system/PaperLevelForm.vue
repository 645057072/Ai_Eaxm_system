<template>
  <el-card>
    <template #header>
      <div class="hdr">
        <el-button link type="primary" @click="router.push('/system/paper-level')">
          <AppEmoji name="back" size="sm" decorative />返回列表
        </el-button>
        <span class="title">{{ isNew ? "新建试卷等级" : "编辑试卷等级" }}</span>
      </div>
    </template>
    <el-form label-width="100px" class="form" @submit.prevent>
      <el-form-item v-if="isNew && auth.isAdmin" label="所属企业" required>
        <el-select v-model="form.enterprise_id" placeholder="请选择企业（与企业信息一致）" filterable style="width: 100%">
          <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="isNew && !auth.isAdmin" label="所属企业">
        <el-input :model-value="teacherEntName" disabled />
      </el-form-item>
      <el-form-item v-if="!isNew" label="所属企业">
        <el-input :model-value="editEnterpriseName" disabled />
      </el-form-item>
      <el-form-item label="等级编号" required>
        <el-input v-model="form.level_code" placeholder="等级编号" />
      </el-form-item>
      <el-form-item label="等级名称" required>
        <el-input v-model="form.level_name" placeholder="等级名称" />
      </el-form-item>
      <el-form-item label="职称系列" required>
        <el-input v-model="form.title_series" placeholder="职称系列" />
      </el-form-item>
      <el-form-item v-if="auth.can('action.paper_level.manage')">
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        <el-button @click="router.push('/system/paper-level')">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { listEnterprises } from "@/api/enterprises";
import { createPaperLevel, getPaperLevel, patchPaperLevel } from "@/api/paper_levels";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

const isNew = computed(() => route.name === "paper-level-new");
const editId = computed(() => {
  const raw = route.params.id as string | undefined;
  if (!raw) return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
});

const enterpriseOpts = ref<{ id: number; name: string }[]>([]);
const editEnterpriseName = ref("");
const saving = ref(false);

const teacherEntName = computed(() => auth.me?.enterprise?.name || "—");

const form = reactive({
  enterprise_id: undefined as number | undefined,
  level_code: "",
  level_name: "",
  title_series: "",
});

async function save() {
  if (!auth.can("action.paper_level.manage")) {
    ElMessage.warning("无维护权限");
    return;
  }
  saving.value = true;
  try {
    if (isNew.value) {
      const body: Record<string, unknown> = {
        level_code: form.level_code,
        level_name: form.level_name,
        title_series: form.title_series,
      };
      if (auth.isAdmin) {
        if (!form.enterprise_id) {
          ElMessage.warning("请选择所属企业");
          return;
        }
        body.enterprise_id = form.enterprise_id;
      }
      await createPaperLevel(body);
      ElMessage.success("已创建");
    } else if (editId.value) {
      await patchPaperLevel(editId.value, {
        level_code: form.level_code,
        level_name: form.level_name,
        title_series: form.title_series,
      });
      ElMessage.success("已保存");
    }
    await router.push("/system/paper-level");
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  if (auth.isAdmin) {
    const { data } = await listEnterprises({ skip: 0, limit: 500 });
    enterpriseOpts.value = (data.items || []) as { id: number; name: string }[];
  }
  if (isNew.value) {
    form.level_code = "";
    form.level_name = "";
    form.title_series = "";
    form.enterprise_id = auth.isAdmin ? enterpriseOpts.value[0]?.id : auth.me?.enterprise_id ?? undefined;
    return;
  }
  const id = editId.value;
  if (!id) {
    ElMessage.error("无效的等级 ID");
    router.replace("/system/paper-level");
    return;
  }
  try {
    const { data } = await getPaperLevel(id);
    form.level_code = data.level_code as string;
    form.level_name = data.level_name as string;
    form.title_series = data.title_series as string;
    editEnterpriseName.value = (data.enterprise_name as string) || "";
  } catch {
    ElMessage.error("加载失败");
    router.replace("/system/paper-level");
  }
});
</script>

<style scoped>
.hdr {
  display: flex;
  align-items: center;
  gap: 16px;
}
.title {
  font-weight: 600;
  color: #1e293b;
}
.form {
  max-width: 560px;
}
</style>
