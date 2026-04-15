import { http } from "./http";

export function listEnterprises(params: { skip?: number; limit?: number; keyword?: string }) {
  return http.get("/v1/enterprises", { params });
}

/** 企业树（仅当前用户可管理范围） */
export function fetchEnterpriseTree() {
  return http.get("/v1/enterprises/tree");
}

export function createEnterprise(body: Record<string, unknown>) {
  return http.post("/v1/enterprises", body);
}

export function patchEnterprise(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/enterprises/${id}`, body);
}

export function deleteEnterprise(id: number) {
  return http.delete(`/v1/enterprises/${id}`);
}

export function uploadEnterpriseLicense(id: number, file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return http.post(`/v1/enterprises/${id}/license`, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}
