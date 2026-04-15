<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title"><AppEmoji name="enterprise" size="sm" decorative />企业信息</div>
      </template>
      <div class="page-list-toolbar toolbar">
        <el-button type="success" @click="openCreate"><AppEmoji name="add" size="sm" decorative />新建企业</el-button>
      </div>
      <div class="page-list-body">
        <div class="page-list-table">
          <el-table
            :data="treeRows"
            row-key="id"
            height="100%"
            style="width: 100%"
            :tree-props="{ children: 'children' }"
            :default-expand-all="false"
          >
            <template #empty>
              <el-empty description="暂无企业档案。" />
            </template>
            <el-table-column prop="enterprise_code" label="企业编码" width="120" show-overflow-tooltip />
            <el-table-column prop="name" label="企业名称" min-width="160" show-overflow-tooltip />
            <el-table-column label="上级单位" min-width="140" show-overflow-tooltip>
              <template #default="{ row }">{{ (row.parent_name as string) || "—" }}</template>
            </el-table-column>
            <el-table-column prop="tax_id" label="纳税人识别号" width="160" show-overflow-tooltip />
            <el-table-column label="营业执照" width="120">
              <template #default="{ row }">
                <template v-if="row.license_file_path">
                  <el-button link type="primary" @click="downloadLicense(row.license_file_path as string)">下载</el-button>
                  <el-button link type="warning" @click="openEdit(row)">重传</el-button>
                </template>
                <el-button v-else link type="primary" @click="openEdit(row)">上传</el-button>
              </template>
            </el-table-column>
            <el-table-column prop="address_phone" label="地址电话" min-width="140" show-overflow-tooltip />
            <el-table-column prop="contact_person" label="联系人" width="100" />
            <el-table-column prop="industry" label="行业信息" min-width="120" show-overflow-tooltip />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEdit(row)"><AppEmoji name="edit" size="sm" decorative />编辑</el-button>
                <el-button link type="danger" @click="onDelete(row)"><AppEmoji name="delete" size="sm" decorative />删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="dlg" :title="editId ? '编辑企业' : '新建企业'" width="600px" @close="uploadFileList = []">
      <el-form label-width="120px">
        <el-form-item label="企业编码" required>
          <el-input v-model="form.enterprise_code" placeholder="全系统唯一编码" />
        </el-form-item>
        <el-form-item label="上级单位">
          <el-select
            v-model="form.parent_id"
            :clearable="auth.isAdmin"
            filterable
            placeholder="选择已存在企业作为上级；无上级可留空（仅全局管理员新建顶级）"
            style="width: 100%"
            @change="onParentChange"
          >
            <el-option v-for="p in parentSelectOpts" :key="p.id" :label="parentOptLabel(p)" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="parentNameDisplay" label="上级名称">
          <el-input :model-value="parentNameDisplay" disabled />
        </el-form-item>
        <el-form-item label="企业名称" required>
          <el-input v-model="form.name" placeholder="企业名称" />
        </el-form-item>
        <el-form-item label="纳税人识别号" required>
          <el-input v-model="form.tax_id" placeholder="纳税人识别号" />
        </el-form-item>
        <el-form-item label="地址电话">
          <el-input v-model="form.address_phone" placeholder="地址、电话" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_person" placeholder="联系人" />
        </el-form-item>
        <el-form-item label="行业信息">
          <el-input v-model="form.industry" type="textarea" :rows="2" placeholder="行业信息" />
        </el-form-item>
        <el-form-item label="营业执照">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="onFileChange"
            :file-list="uploadFileList"
            accept=".pdf,.jpg,.jpeg,.png,.webp"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 pdf/jpg/png/webp，最大 10MB；新建时在保存时一并上传</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import type { UploadFile, UploadFiles } from "element-plus";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage, http } from "@/api/http";
import {
  fetchEnterpriseTree,
  createEnterprise,
  patchEnterprise,
  deleteEnterprise,
  uploadEnterpriseLicense,
} from "@/api/enterprises";
import { useAuthStore } from "@/stores/auth";

type TreeRow = Record<string, unknown> & { children?: TreeRow[] };

const auth = useAuthStore();

const treeRows = ref<TreeRow[]>([]);
/** 扁平上级候选（含 id/name/parent_name便于展示） */
const flatEnts = ref<{ id: number; name: string; parent_name?: string | null }[]>([]);

const dlg = ref(false);
const editId = ref<number | null>(null);
const pendingFile = ref<File | null>(null);
const uploadFileList = ref<UploadFiles>([]);

const form = reactive({
  enterprise_code: "",
  parent_id: null as number | null,
  name: "",
  tax_id: "",
  address_phone: "",
  contact_person: "",
  industry: "",
});

const parentNameDisplay = ref("");

function flattenTree(nodes: TreeRow[], out: { id: number; name: string; parent_name?: string | null }[]) {
  for (const n of nodes) {
    out.push({
      id: n.id as number,
      name: (n.name as string) || "",
      parent_name: (n.parent_name as string) || null,
    });
    const ch = n.children as TreeRow[] | undefined;
    if (ch?.length) flattenTree(ch, out);
  }
}

function parentOptLabel(p: { id: number; name: string; parent_name?: string | null }) {
  if (p.parent_name) return `${p.name}（上级：${p.parent_name}）`;
  return p.name;
}

/** 新建时选上级：排除自身（编辑时） */
const parentSelectOpts = computed(() => {
  const self = editId.value;
  return flatEnts.value.filter((e) => e.id !== self);
});

function onParentChange(pid: number | null | undefined) {
  if (pid == null) {
    parentNameDisplay.value = "";
    return;
  }
  const hit = flatEnts.value.find((e) => e.id === pid);
  parentNameDisplay.value = hit?.name || "";
}

async function load() {
  try {
    const { data } = await fetchEnterpriseTree();
    const roots = (data || []) as TreeRow[];
    treeRows.value = roots;
    const flat: { id: number; name: string; parent_name?: string | null }[] = [];
    flattenTree(roots, flat);
    flatEnts.value = flat;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载企业树失败"));
    treeRows.value = [];
    flatEnts.value = [];
  }
}

function openCreate() {
  editId.value = null;
  form.enterprise_code = "";
  form.parent_id = null;
  form.name = "";
  form.tax_id = "";
  form.address_phone = "";
  form.contact_person = "";
  form.industry = "";
  parentNameDisplay.value = "";
  pendingFile.value = null;
  uploadFileList.value = [];
  dlg.value = true;
}

function openEdit(row: Record<string, unknown>) {
  editId.value = row.id as number;
  form.enterprise_code = (row.enterprise_code as string) || "";
  form.parent_id = (row.parent_id as number) || null;
  form.name = (row.name as string) || "";
  form.tax_id = (row.tax_id as string) || "";
  form.address_phone = (row.address_phone as string) || "";
  form.contact_person = (row.contact_person as string) || "";
  form.industry = (row.industry as string) || "";
  parentNameDisplay.value = ((row.parent_name as string) || "").trim();
  pendingFile.value = null;
  uploadFileList.value = [];
  dlg.value = true;
}

function onFileChange(_file: UploadFile, fileList: UploadFiles) {
  uploadFileList.value = fileList;
  const raw = fileList[0]?.raw;
  pendingFile.value = raw ?? null;
}

async function save() {
  const code = form.enterprise_code.trim();
  if (!code || !form.name.trim() || !form.tax_id.trim()) {
    ElMessage.warning("请填写企业编码、企业名称与纳税人识别号");
    return;
  }
  if (!editId.value && !auth.isAdmin && (form.parent_id == null || form.parent_id === undefined)) {
    ElMessage.warning("非全局管理员新建企业须选择上级单位");
    return;
  }
  try {
    if (!editId.value) {
      const { data } = await createEnterprise({
        enterprise_code: code,
        parent_id: form.parent_id,
        name: form.name.trim(),
        tax_id: form.tax_id.trim(),
        address_phone: form.address_phone.trim() || null,
        contact_person: form.contact_person.trim() || null,
        industry: form.industry.trim() || null,
      });
      editId.value = data.id;
      ElMessage.success("已创建");
      if (pendingFile.value) {
        await uploadEnterpriseLicense(data.id, pendingFile.value);
        ElMessage.success("营业执照已上传");
      }
    } else {
      const body: Record<string, unknown> = {
        enterprise_code: code,
        parent_id: form.parent_id,
        name: form.name.trim(),
        tax_id: form.tax_id.trim(),
        address_phone: form.address_phone.trim() || null,
        contact_person: form.contact_person.trim() || null,
        industry: form.industry.trim() || null,
      };
      await patchEnterprise(editId.value, body);
      if (pendingFile.value) {
        await uploadEnterpriseLicense(editId.value, pendingFile.value);
        ElMessage.success("营业执照已上传");
      }
      ElMessage.success("已保存");
    }
    dlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

async function downloadLicense(filename: string) {
  const { data } = await http.get(`/v1/files/${encodeURIComponent(filename)}`, { responseType: "blob" });
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

async function onDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm("确定删除该企业？", "提示", { type: "warning" });
  await deleteEnterprise(row.id as number);
  ElMessage.success("已删除");
  await load();
}

onMounted(load);
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
}
</style>
