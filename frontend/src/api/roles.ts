import { http } from "./http";

export function listRoles() {
  return http.get("/v1/roles");
}

export function getRole(id: number) {
  return http.get(`/v1/roles/${id}`);
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

export function fetchRolePermissions(roleId: number) {
  return http.get<string[]>(`/v1/roles/${roleId}/permissions`);
}

export function saveRolePermissions(roleId: number, codes: string[]) {
  return http.put<string[]>(`/v1/roles/${roleId}/permissions`, { codes });
}
