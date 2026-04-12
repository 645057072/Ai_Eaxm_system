import axios, { type AxiosError } from "axios";

const baseURL = import.meta.env.VITE_API_BASE || "/api";

/** 解析 FastAPI / 通用后端错误信息，供表单提示 */
export function apiErrorMessage(err: unknown, fallback = "请求失败"): string {
  const e = err as AxiosError<{ detail?: string | Array<{ msg?: string }> }>;
  const d = e.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d.length) {
    const parts = d.map((x) => (typeof x === "object" && x && "msg" in x ? String((x as { msg?: string }).msg) : ""));
    const joined = parts.filter(Boolean).join("; ");
    if (joined) return joined;
  }
  return fallback;
}

export const http = axios.create({
  baseURL,
  timeout: 60000,
});

const TOKEN_KEY = "exam_token";

http.interceptors.request.use((config) => {
  const t = localStorage.getItem(TOKEN_KEY);
  if (t) {
    config.headers.Authorization = `Bearer ${t}`;
  }
  return config;
});

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      if (!window.location.hash.includes("login")) {
        window.location.hash = "#/login";
      }
    }
    return Promise.reject(err);
  }
);

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}
