import { http } from "./http";

export function listRoles() {
  return http.get("/v1/roles");
}

export function createRole(body: Record<string, unknown>) {
  return http.post("/v1/roles", body);
}

export function patchRole(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/roles/${id}`, body);
}

export function deleteRole(id: number) {
  return http.delete(`/v1/roles/${id}`);
}
