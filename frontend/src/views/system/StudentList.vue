<template>
  <div class="fill-height">
    <el-card class="page-list-card">
      <template #header>
        <div class="page-list-card-title"><AppEmoji name="roleStudent" size="sm" decorative />学员管理</div>
      </template>

      <div class="page-list-toolbar toolbar">
        <el-select
          v-if="auth.isAdmin"
          v-model="filterEnterpriseId"
          clearable
          filterable
          placeholder="所属企业"
          style="width: 180px"
          @change="doSearch"
        >
          <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-input v-model="kwNo" clearable placeholder="学员编号" style="width: 160px" @keyup.enter="doSearch" />
        <el-input v-model="kwName" clearable placeholder="姓名" style="width: 140px" @keyup.enter="doSearch" />
        <el-input v-model="kwCompany" clearable placeholder="所属公司" style="width: 180px" @keyup.enter="doSearch" />
        <el-button type="primary" @click="doSearch"><AppEmoji name="search" size="sm" decorative />查询</el-button>
        <el-button v-if="auth.can('action.student.create')" type="success" @click="openCreate"
          ><AppEmoji name="add" size="sm" decorative />新建学员</el-button
        >
        <el-button v-if="auth.can('action.student.import')" type="warning" @click="openImport">导入信息</el-button>
      </div>

      <div class="page-list-body">
        <div class="page-list-table">
          <el-table :data="rows" height="100%" style="width: 100%">
            <template #empty>
              <el-empty description="暂无学员数据" />
            </template>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="student_no" label="学员编号" width="140" show-overflow-tooltip />
            <el-table-column prop="full_name" label="姓名" width="120" show-overflow-tooltip />
            <el-table-column prop="gender" label="性别" width="80" align="center" />
            <el-table-column prop="birth_month" label="出生年月" width="110" align="center" />
            <el-table-column prop="company_name" label="所属公司" min-width="160" show-overflow-tooltip />
            <el-table-column v-if="auth.isAdmin" prop="enterprise_name" label="所属企业" width="160" show-overflow-tooltip />
            <el-table-column prop="phone" label="联系电话" width="140" show-overflow-tooltip />
            <el-table-column prop="id_card_no" label="身份证号" width="180" show-overflow-tooltip />
            <el-table-column prop="address_phone" label="地址电话" min-width="160" show-overflow-tooltip />
            <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button v-if="auth.can('action.student.update')" link type="primary" @click="openEdit(row)"
                  ><AppEmoji name="edit" size="sm" decorative />编辑</el-button
                >
                <el-button v-if="auth.can('action.student.delete')" link type="danger" @click="onDelete(row)"
                  ><AppEmoji name="delete" size="sm" decorative />删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="page-list-pager">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next"
            :total="total"
            :page-size="limit"
            :current-page="page"
            :page-sizes="[15, 50, 100, 200]"
            @current-change="onPagerPageChange"
            @size-change="onPageSizeChange"
          />
        </div>
      </div>
    </el-card>

    <el-dialog v-model="dlg" :title="editId ? '编辑学员' : '新建学员'" width="720px" @closed="onDlgClosed">
      <el-form label-width="110px">
        <el-form-item v-if="auth.isAdmin" label="所属企业">
          <el-select v-model="form.enterprise_id" clearable filterable placeholder="可选" style="width: 100%">
            <el-option v-for="e in enterpriseOpts" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学员编号" required>
          <el-input v-model="form.student_no" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="form.full_name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="form.gender" clearable placeholder="可选" style="width: 100%">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
            <el-option label="未知" value="未知" />
          </el-select>
        </el-form-item>
        <el-form-item label="出生年月">
          <el-date-picker v-model="form.birth_month" type="month" value-format="YYYY-MM" style="width: 100%" />
        </el-form-item>
        <el-form-item label="所属公司">
          <el-input v-model="form.company_name" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="身份证号">
          <el-input v-model="form.id_card_no" />
        </el-form-item>
        <el-form-item label="地址电话">
          <el-input v-model="form.address_phone" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDlg" title="导入学员信息" width="560px" @closed="resetImport">
      <div class="import-box">
        <input ref="fileInput" type="file" multiple :accept="acceptTypes" @change="onPickFiles" />
        <p class="hint-text">支持 word/excel/pdf/图片/csv/txt；单个文件 ≤20MB，可多选。</p>
        <p v-if="importFiles.length" class="hint-text">已选 {{ importFiles.length }} 个文件</p>
      </div>
      <template #footer>
        <el-button @click="importDlg = false">取消</el-button>
        <el-button type="primary" :loading="importLoading" @click="submitImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiErrorMessage } from "@/api/http";
import { listStudents, createStudent, patchStudent, deleteStudent, importStudents } from "@/api/students";
import { listEnterprises } from "@/api/enterprises";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);
const page = ref(1);
const limit = ref(15);

const filterEnterpriseId = ref<number | undefined>();
const enterpriseOpts = ref<{ id: number; name: string }[]>([]);

const kwNo = ref("");
const kwName = ref("");
const kwCompany = ref("");

const dlg = ref(false);
const editId = ref<number | null>(null);
const form = reactive({
  enterprise_id: null as number | null,
  student_no: "",
  full_name: "",
  gender: "" as string | "",
  birth_month: "" as string | "",
  company_name: "",
  phone: "",
  id_card_no: "",
  address_phone: "",
  remark: "",
});

async function load() {
  const skip = (page.value - 1) * limit.value;
  const params: Record<string, unknown> = { skip, limit: limit.value };
  if (auth.isAdmin && filterEnterpriseId.value) params.enterprise_id = filterEnterpriseId.value;
  const a = kwNo.value.trim();
  const b = kwName.value.trim();
  const c = kwCompany.value.trim();
  if (a) params.student_keyword = a;
  if (b) params.name_keyword = b;
  if (c) params.company_keyword = c;
  try {
    const { data } = await listStudents(params);
    total.value = data.total;
    rows.value = data.items;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "加载失败"));
  }
}

function doSearch() {
  page.value = 1;
  void load();
}

function onPagerPageChange(p: number) {
  page.value = p;
  void load();
}

function onPageSizeChange(sz: number) {
  limit.value = sz;
  page.value = 1;
  void load();
}

function openCreate() {
  editId.value = null;
  form.enterprise_id = auth.isAdmin ? enterpriseOpts.value[0]?.id ?? null : null;
  form.student_no = "";
  form.full_name = "";
  form.gender = "";
  form.birth_month = "";
  form.company_name = "";
  form.phone = "";
  form.id_card_no = "";
  form.address_phone = "";
  form.remark = "";
  dlg.value = true;
}

function openEdit(row: Record<string, unknown>) {
  editId.value = row.id as number;
  form.enterprise_id = (row.enterprise_id as number) ?? null;
  form.student_no = (row.student_no as string) || "";
  form.full_name = (row.full_name as string) || "";
  form.gender = ((row.gender as string) || "") as any;
  form.birth_month = ((row.birth_month as string) || "") as any;
  form.company_name = (row.company_name as string) || "";
  form.phone = (row.phone as string) || "";
  form.id_card_no = (row.id_card_no as string) || "";
  form.address_phone = (row.address_phone as string) || "";
  form.remark = (row.remark as string) || "";
  dlg.value = true;
}

function onDlgClosed() {
  editId.value = null;
}

async function save() {
  if (!form.student_no.trim()) return ElMessage.warning("请填写学员编号");
  if (!form.full_name.trim()) return ElMessage.warning("请填写姓名");
  const body: Record<string, unknown> = {
    student_no: form.student_no.trim(),
    full_name: form.full_name.trim(),
    gender: form.gender || null,
    birth_month: form.birth_month || null,
    company_name: form.company_name.trim() || null,
    phone: form.phone.trim() || null,
    id_card_no: form.id_card_no.trim() || null,
    address_phone: form.address_phone.trim() || null,
    remark: form.remark.trim() || null,
  };
  if (auth.isAdmin) body.enterprise_id = form.enterprise_id;
  try {
    if (!editId.value) await createStudent(body);
    else await patchStudent(editId.value, body);
    ElMessage.success("已保存");
    dlg.value = false;
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "保存失败"));
  }
}

async function onDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm("确定删除该学员？", "提示", { type: "warning" });
  try {
    await deleteStudent(row.id as number);
    ElMessage.success("已删除");
    await load();
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "删除失败"));
  }
}

// 导入
const importDlg = ref(false);
const importFiles = ref<File[]>([]);
const importLoading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

const acceptTypes =
  ".doc,.docx,.xls,.xlsx,.pdf,.png,.jpg,.jpeg,.webp,.csv,.txt,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/pdf,image/*,text/csv,text/plain";

function openImport() {
  importFiles.value = [];
  importDlg.value = true;
  setTimeout(() => fileInput.value?.focus(), 0);
}

function onPickFiles(e: Event) {
  const t = e.target as HTMLInputElement;
  importFiles.value = t.files?.length ? Array.from(t.files) : [];
}

function resetImport() {
  importFiles.value = [];
  importLoading.value = false;
  if (fileInput.value) fileInput.value.value = "";
}

async function submitImport() {
  if (!importFiles.value.length) return ElMessage.warning("请选择文件");
  importLoading.value = true;
  try {
    const fd = new FormData();
    for (const f of importFiles.value) fd.append("files", f);
    const { data } = await importStudents(fd);
    ElMessage.success(`已上传 ${data.count || importFiles.value.length} 个文件`);
    importDlg.value = false;
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, "导入失败"));
  } finally {
    importLoading.value = false;
  }
}

/** 关键字变更后短暂防抖自动查询 */
const suppressFilterWatch = ref(true);
let filterDebounce: ReturnType<typeof setTimeout> | null = null;
watch([kwNo, kwName, kwCompany], () => {
  if (suppressFilterWatch.value) return;
  if (filterDebounce) clearTimeout(filterDebounce);
  filterDebounce = setTimeout(() => {
    filterDebounce = null;
    doSearch();
  }, 400);
});

onMounted(async () => {
  if (auth.isAdmin) {
    try {
      const { data } = await listEnterprises({ skip: 0, limit: 200 });
      enterpriseOpts.value = (data.items || []).map((e: { id: number; name: string }) => ({ id: e.id, name: e.name }));
      filterEnterpriseId.value = enterpriseOpts.value[0]?.id;
    } catch {
      enterpriseOpts.value = [];
      filterEnterpriseId.value = undefined;
    }
  }
  await load();
  suppressFilterWatch.value = false;
});
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.import-box input[type="file"] {
  display: block;
}
.hint-text {
  margin: 10px 0 0;
  font-size: 12px;
  color: #64748b;
}
</style>

