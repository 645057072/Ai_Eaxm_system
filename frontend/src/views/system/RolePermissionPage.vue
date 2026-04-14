<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="hdr">
          <span class="title">功能授权 — {{ roleName }}（{{ roleCode }}）</span>
          <div class="hdr-act">
            <el-button link type="primary" @click="router.push('/system/roles')">
              <AppEmoji name="back" size="sm" decorative />返回列表
            </el-button>
            <el-button link type="info" @click="closePage">
              <AppEmoji name="close" size="sm" decorative />关闭
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="loading" class="role-perm-loading">加载中...</div>
      <template v-else>
        <div class="page-list-body role-perm-body">
          <div class="page-list-sticky-block">
            <p class="tip">
              树形勾选菜单、列表、表单、字段与操作；列表/表单行右侧「含下级」勾选后，勾选该行将同步勾选其下全部字段（取消同理）。
            </p>
          </div>
          <div class="role-perm-tree-scroll">
            <div class="tree-panel">
        <div v-for="mod in authModules" :key="mod.moduleKey" class="mod-block">
          <div class="mod-title">
            <el-checkbox
              v-if="mod.moduleCode"
              :model-value="has(mod.moduleCode)"
              class="mod-check"
              @change="(v: boolean | string | number) => toggleCode(mod.moduleCode as string, !!v)"
            >
              {{ mod.moduleTitle }}
            </el-checkbox>
            <span v-else>{{ mod.moduleTitle }}</span>
          </div>

          <template v-if="mod.menus.length">
            <div v-for="m in mod.menus" :key="m.code" class="menu-block">
              <div class="tree-line depth-1 menu-line">
                <el-checkbox :model-value="has(m.code)" @change="(v: boolean | string | number) => toggleCode(m.code, !!v)">
                  {{ m.name }}
                </el-checkbox>
              </div>

              <template v-if="formsForMenu(mod, m).length">
                <div class="kind-label depth-2">表单</div>
                <div v-for="row in formsForMenu(mod, m)" :key="'f-' + row.item.code" class="lf-wrap">
                  <div class="tree-line depth-2 row-with-sub">
                    <el-checkbox
                      :model-value="has(row.item.code)"
                      @change="(v: boolean | string | number) => onListFormCheck(row, 'form', !!v)"
                    >
                      {{ row.item.name }}
                    </el-checkbox>
                    <el-checkbox
                      v-if="row.fields.length"
                      v-model="includeSub[row.item.code]"
                      class="sub-check"
                      @change="() => onIncludeSubToggle(row)"
                    >
                      含下级
                    </el-checkbox>
                  </div>
                  <div v-for="f in row.fields" :key="f.code" class="tree-line depth-3">
                    <el-checkbox :model-value="has(f.code)" @change="(v: boolean | string | number) => toggleCode(f.code, !!v)">
                      {{ f.name }}
                    </el-checkbox>
                  </div>
                </div>
              </template>

              <template v-if="listsForMenu(mod, m).length">
                <div class="kind-label depth-2">列表</div>
                <div v-for="row in listsForMenu(mod, m)" :key="'l-' + row.item.code" class="lf-wrap">
                  <div class="tree-line depth-2 row-with-sub">
                    <el-checkbox
                      :model-value="has(row.item.code)"
                      @change="(v: boolean | string | number) => onListFormCheck(row, 'list', !!v)"
                    >
                      {{ row.item.name }}
                    </el-checkbox>
                    <el-checkbox
                      v-if="row.fields.length"
                      v-model="includeSub[row.item.code]"
                      class="sub-check"
                      @change="() => onIncludeSubToggle(row)"
                    >
                      含下级
                    </el-checkbox>
                  </div>
                  <div v-for="f in row.fields" :key="f.code" class="tree-line depth-3">
                    <el-checkbox :model-value="has(f.code)" @change="(v: boolean | string | number) => toggleCode(f.code, !!v)">
                      {{ f.name }}
                    </el-checkbox>
                  </div>
                </div>
              </template>

              <template v-if="actionsForMenu(mod, m).length">
                <div class="kind-label depth-2">操作</div>
                <div v-for="a in actionsForMenu(mod, m)" :key="a.code" class="tree-line depth-2">
                  <el-checkbox :model-value="has(a.code)" @change="(v: boolean | string | number) => toggleCode(a.code, !!v)">
                    {{ a.name }}
                  </el-checkbox>
                </div>
              </template>
            </div>
          </template>

          <template v-else>
            <template v-if="mod.forms.length">
              <div class="kind-label">表单</div>
              <div v-for="row in mod.forms" :key="'f-' + row.item.code" class="lf-wrap">
                <div class="tree-line depth-1 row-with-sub">
                  <el-checkbox
                    :model-value="has(row.item.code)"
                    @change="(v: boolean | string | number) => onListFormCheck(row, 'form', !!v)"
                  >
                    {{ row.item.name }}
                  </el-checkbox>
                  <el-checkbox
                    v-if="row.fields.length"
                    v-model="includeSub[row.item.code]"
                    class="sub-check"
                    @change="() => onIncludeSubToggle(row)"
                  >
                    含下级
                  </el-checkbox>
                </div>
                <div v-for="f in row.fields" :key="f.code" class="tree-line depth-2">
                  <el-checkbox :model-value="has(f.code)" @change="(v: boolean | string | number) => toggleCode(f.code, !!v)">
                    {{ f.name }}
                  </el-checkbox>
                </div>
              </div>
            </template>

            <template v-if="mod.lists.length">
              <div class="kind-label">列表</div>
              <div v-for="row in mod.lists" :key="'l-' + row.item.code" class="lf-wrap">
                <div class="tree-line depth-1 row-with-sub">
                  <el-checkbox
                    :model-value="has(row.item.code)"
                    @change="(v: boolean | string | number) => onListFormCheck(row, 'list', !!v)"
                  >
                    {{ row.item.name }}
                  </el-checkbox>
                  <el-checkbox
                    v-if="row.fields.length"
                    v-model="includeSub[row.item.code]"
                    class="sub-check"
                    @change="() => onIncludeSubToggle(row)"
                  >
                    含下级
                  </el-checkbox>
                </div>
                <div v-for="f in row.fields" :key="f.code" class="tree-line depth-2">
                  <el-checkbox :model-value="has(f.code)" @change="(v: boolean | string | number) => toggleCode(f.code, !!v)">
                    {{ f.name }}
                  </el-checkbox>
                </div>
              </div>
            </template>

            <template v-if="mod.actions.length">
              <div class="kind-label">操作</div>
              <div v-for="a in mod.actions" :key="a.code" class="tree-line depth-1">
                <el-checkbox :model-value="has(a.code)" @change="(v: boolean | string | number) => toggleCode(a.code, !!v)">
                  {{ a.name }}
                </el-checkbox>
              </div>
            </template>
          </template>
            </div>
          </div>
          </div>
          <div class="footer-act">
            <el-button type="primary" :loading="saving" @click="savePerm">保存授权</el-button>
          </div>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { fetchPermissionCatalog, type AuthModulePayload, type CatalogItem } from "@/api/permissions";
import { fetchRolePermissions, getRole, saveRolePermissions } from "@/api/roles";

defineOptions({ name: "RolePermissionPage" });

type LfRow = { item: CatalogItem; fields: CatalogItem[] };

const route = useRoute();
const router = useRouter();

const roleId = computed(() => Number(route.params.roleId));
const roleName = ref("");
const roleCode = ref("");
const loading = ref(true);
const saving = ref(false);
const authModules = ref<AuthModulePayload[]>([]);
const selectedList = ref<string[]>([]);
const includeSub = reactive<Record<string, boolean>>({});
const loadedRoleId = ref<number | null>(null);

function formsForMenu(mod: AuthModulePayload, m: CatalogItem) {
  return mod.forms.filter((row) => row.item.label === m.name);
}

function listsForMenu(mod: AuthModulePayload, m: CatalogItem) {
  return mod.lists.filter((row) => row.item.label === m.name);
}

function actionsForMenu(mod: AuthModulePayload, m: CatalogItem) {
  return mod.actions.filter((a) => a.label === m.name);
}

function closePage() {
  // 关闭：返回角色列表；页面被 keep-alive 缓存，未主动清空表单/勾选
  router.push("/system/roles");
}

function has(code: string) {
  return selectedList.value.includes(code);
}

function toggleCode(code: string, on: boolean) {
  if (on) {
    if (!selectedList.value.includes(code)) selectedList.value.push(code);
  } else {
    selectedList.value = selectedList.value.filter((c) => c !== code);
  }
}

function onListFormCheck(row: LfRow, _kind: "list" | "form", checked: boolean) {
  toggleCode(row.item.code, checked);
  if (includeSub[row.item.code] && row.fields.length) {
    for (const f of row.fields) {
      toggleCode(f.code, checked);
    }
  }
}

function onIncludeSubToggle(row: LfRow) {
  if (!has(row.item.code) || !row.fields.length) return;
  if (includeSub[row.item.code]) {
    for (const f of row.fields) {
      if (!has(f.code)) toggleCode(f.code, true);
    }
  } else {
    for (const f of row.fields) {
      toggleCode(f.code, false);
    }
  }
}

function syncIncludeSubFlags() {
  for (const mod of authModules.value) {
    for (const row of mod.lists) {
      if (!row.fields.length) continue;
      const allFieldsOn = row.fields.every((f) => has(f.code));
      includeSub[row.item.code] = has(row.item.code) && allFieldsOn;
    }
    for (const row of mod.forms) {
      if (!row.fields.length) continue;
      const allFieldsOn = row.fields.every((f) => has(f.code));
      includeSub[row.item.code] = has(row.item.code) && allFieldsOn;
    }
  }
}

async function load() {
  loading.value = true;
  try {
    const id = roleId.value;
    if (!Number.isFinite(id) || id < 1) {
      ElMessage.error("无效的角色");
      router.replace("/system/roles");
      return;
    }
    const [{ data: role }, { data: cat }, { data: codes }] = await Promise.all([
      getRole(id),
      fetchPermissionCatalog(),
      fetchRolePermissions(id),
    ]);
    roleName.value = role.name as string;
    roleCode.value = role.code as string;
    authModules.value = cat.authModules?.length ? cat.authModules : [];
    selectedList.value = [...codes];
    Object.keys(includeSub).forEach((k) => delete includeSub[k]);
    syncIncludeSubFlags();
    loadedRoleId.value = id;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载失败"));
    router.replace("/system/roles");
  } finally {
    loading.value = false;
  }
}

async function savePerm() {
  const id = roleId.value;
  saving.value = true;
  try {
    await saveRolePermissions(id, selectedList.value);
    ElMessage.success("已保存功能授权（页面未关闭，可继续调整）");
    syncIncludeSubFlags();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  } finally {
    saving.value = false;
  }
}

watch(
  roleId,
  async (id) => {
    if (!id || !Number.isFinite(id) || id < 1) return;
    if (loadedRoleId.value === id && !loading.value) return;
    await load();
  },
  { immediate: true },
);

onActivated(() => {
  // keep-alive 恢复时不强制 reload，保留用户当前勾选状态
});
</script>

<style scoped>
.hdr {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.hdr-act {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}
.title {
  font-weight: 600;
  color: #1e293b;
}
.role-perm-loading {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
}
.role-perm-tree-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.tip {
  font-size: 13px;
  color: #64748b;
  line-height: 1.55;
  margin: 0 0 16px;
}
.tree-panel {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 16px;
  background: #fafbfc;
}
.mod-block {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #cbd5e1;
}
.mod-block:last-child {
  border-bottom: none;
  margin-bottom: 0;
}
.mod-title {
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 10px;
  font-size: 15px;
}
.mod-check :deep(.el-checkbox__label) {
  font-weight: 700;
  color: #0f172a;
  font-size: 15px;
}
.menu-line {
  font-weight: 600;
  color: #1e293b;
}
.kind-label {
  font-size: 12px;
  color: #94a3b8;
  margin: 8px 0 4px;
  padding-left: 4px;
}
.kind-label.depth-2 {
  padding-left: 36px;
  margin-top: 6px;
}
.tree-line {
  padding: 4px 0 4px 8px;
  display: flex;
  align-items: center;
}
.depth-1 {
  padding-left: 12px;
}
.row-with-sub {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  width: 100%;
  gap: 8px;
}
.depth-2 {
  padding-left: 36px;
  border-left: 2px solid #e2e8f0;
  margin-left: 10px;
}
.depth-3 {
  padding-left: 60px;
  border-left: 2px solid #e2e8f0;
  margin-left: 20px;
}
.lf-wrap {
  margin-bottom: 8px;
}
.row-with-sub {
  gap: 16px;
}
.sub-check {
  margin-left: auto;
  flex-shrink: 0;
}
.footer-act {
  flex-shrink: 0;
  margin-top: 12px;
  padding-top: 4px;
}
</style>
