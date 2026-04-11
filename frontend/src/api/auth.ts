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
