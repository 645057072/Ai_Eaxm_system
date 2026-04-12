import { http } from "./http";

export function login(username: string, password: string) {
  return http.post<{ access_token: string; token_type: string }>("/v1/auth/login", {
    username,
    password,
  });
}

export function fetchMe() {
  return http.get("/v1/auth/me");
}

export function changeMyPassword(old_password: string, new_password: string) {
  return http.patch("/v1/auth/me/password", { old_password, new_password });
}
