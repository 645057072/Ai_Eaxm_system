import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE || "/api";

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
