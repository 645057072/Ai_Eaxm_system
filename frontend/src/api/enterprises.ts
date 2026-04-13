import { http } from "./http";

export function listEnterprises(params: { skip?: number; limit?: number; keyword?: string }) {
  return http.get("/v1/enterprises", { params });
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
