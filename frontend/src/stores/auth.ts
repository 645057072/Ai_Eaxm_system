import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { setToken } from "@/api/http";
import { login as apiLogin, fetchMe } from "@/api/auth";

function readToken() {
  return localStorage.getItem("exam_token") || "";
}

export const useAuthStore = defineStore("auth", () => {
  const token = ref(readToken());
  const me = ref<{
    id: number;
    username: string;
    full_name: string | null;
    role: { id: number; name: string; code: string };
  } | null>(null);

  const roleCode = computed(() => me.value?.role?.code || "");
  const isAdmin = computed(() => roleCode.value === "admin");
  const isTeacher = computed(() => roleCode.value === "teacher" || roleCode.value === "admin");
  const isStudent = computed(() => roleCode.value === "student");

  async function login(username: string, password: string) {
    const { data } = await apiLogin(username, password);
    token.value = data.access_token;
    setToken(data.access_token);
    await loadMe();
  }

  async function loadMe() {
    const { data } = await fetchMe();
    me.value = data;
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
    login,
    loadMe,
    logout,
  };
});
