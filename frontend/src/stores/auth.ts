import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { setToken } from "@/api/http";
import { login as apiLogin, fetchMe } from "@/api/auth";

function readToken() {
  return localStorage.getItem("exam_token") || "";
}

export type Me = {
  id: number;
  username: string;
  full_name: string | null;
  enterprise_id: number;
  enterprise: { id: number; name: string };
  role: { id: number; name: string; code: string };
  permissions: string[];
};

export const useAuthStore = defineStore("auth", () => {
  const token = ref(readToken());
  const me = ref<Me | null>(null);

  const roleCode = computed(() => me.value?.role?.code || "");

  /** 与后端一致：内置管理员角色，功能点校验走 * 或全量 */
  const isAdmin = computed(() => roleCode.value === "admin");
  const isTeacher = computed(() => roleCode.value === "teacher" || roleCode.value === "admin");
  const isStudent = computed(() => roleCode.value === "student");

  /** 是否具备功能点（与后端 permission_match 对齐） */
  function can(code: string): boolean {
    const perms = me.value?.permissions;
    if (!perms?.length) return false;
    if (perms.includes("*")) return true;
    if (perms.includes(code)) return true;
    for (const g of perms) {
      if (code.startsWith(g + ".")) return true;
    }
    if (code.startsWith("field.user.") && perms.includes("form.user")) return true;
    if (code.startsWith("field.enterprise.") && perms.includes("form.enterprise")) return true;
    return false;
  }

  function canAny(...codes: string[]): boolean {
    return codes.some((c) => can(c));
  }

  async function login(username: string, password: string) {
    const { data } = await apiLogin(username, password);
    token.value = data.access_token;
    setToken(data.access_token);
    await loadMe();
  }

  async function loadMe() {
    const { data } = await fetchMe();
    me.value = data as Me;
  }

  function logout() {
    setToken(null);
    token.value = "";
    me.value = null;
  }

  return {
    token,
    me,
    roleCode,
    isAdmin,
    isTeacher,
    isStudent,
    can,
    canAny,
    login,
    loadMe,
    logout,
  };
});
