import { http } from "./http";

export function listUsers(params: { skip?: number; limit?: number; keyword?: string }) {
  return http.get("/v1/users", { params });
}

export function createUser(body: Record<string, unknown>) {
  return http.post("/v1/users", body);
}

export function patchUser(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/users/${id}`, body);
}

export function deleteUser(id: number) {
  return http.delete(`/v1/users/${id}`);
}
