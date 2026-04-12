<template>
  <el-card>
    <div class="toolbar">
      <el-button type="success" @click="openCreate"><AppEmoji name="add" size="sm" decorative />新建企业</el-button>
    </div>
    <el-table :data="rows" style="width: 100%">
      <template #empty>
        <el-empty description="暂无企业档案。本列表仅展示当前账号所属企业；新建后若仍无数据，请确认账号 enterprise_id 与库中企业记录一致。" />
      </template>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="企业名称" min-width="140" show-overflow-tooltip />
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
    <div class="pager">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="limit"
        @current-change="(p: number) => { page = p; load(); }"
      />
    </div>

    <el-dialog v-model="dlg" :title="editId ? '编辑企业' : '新建企业'" width="560px" @close="uploadFileList = []">
      <el-form label-width="120px">
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
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import type { UploadFile, UploadFiles } from "element-plus";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage, http } from "@/api/http";
import {
  listEnterprises,
  createEnterprise,
  patchEnterprise,
  deleteEnterprise,
  uploadEnterpriseLicense,
} from "@/api/enterprises";

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(20);

const dlg = ref(false);
const editId = ref<number | null>(null);
const pendingFile = ref<File | null>(null);
const uploadFileList = ref<UploadFiles>([]);

const form = reactive({
  name: "",
  tax_id: "",
  address_phone: "",
  contact_person: "",
  industry: "",
});

async function load() {
  try {
    const skip = (page.value - 1) * limit.value;
    const { data } = await listEnterprises({ skip, limit: limit.value });
    total.value = data.total;
    rows.value = data.items;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载企业列表失败"));
    total.value = 0;
    rows.value = [];
  }
}

function openCreate() {
  editId.value = null;
  form.name = "";
  form.tax_id = "";
  form.address_phone = "";
  form.contact_person = "";
  form.industry = "";
  pendingFile.value = null;
  uploadFileList.value = [];
  dlg.value = true;
}

function openEdit(row: Record<string, unknown>) {
  editId.value = row.id as number;
  form.name = (row.name as string) || "";
  form.tax_id = (row.tax_id as string) || "";
  form.address_phone = (row.address_phone as string) || "";
  form.contact_person = (row.contact_person as string) || "";
  form.industry = (row.industry as string) || "";
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
  if (!form.name.trim() || !form.tax_id.trim()) {
    ElMessage.warning("请填写企业名称与纳税人识别号");
    return;
  }
  try {
    if (!editId.value) {
      const { data } = await createEnterprise({
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
      await patchEnterprise(editId.value, {
        name: form.name.trim(),
        tax_id: form.tax_id.trim(),
        address_phone: form.address_phone.trim() || null,
        contact_person: form.contact_person.trim() || null,
        industry: form.industry.trim() || null,
      });
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
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
