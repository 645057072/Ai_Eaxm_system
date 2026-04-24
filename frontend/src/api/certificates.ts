import { http } from "./http";

export function listCertTemplates(params: {
  skip?: number;
  limit?: number;
  keyword?: string;
  enterprise_id?: number;
}) {
  return http.get("/v1/certificates/templates", { params });
}

export function getCertTemplate(id: number) {
  return http.get(`/v1/certificates/templates/${id}`);
}

export function createCertTemplate(body: Record<string, unknown>) {
  return http.post("/v1/certificates/templates", body);
}

export function patchCertTemplate(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/certificates/templates/${id}`, body);
}

export function deleteCertTemplate(id: number) {
  return http.delete(`/v1/certificates/templates/${id}`);
}

export function listCertRecords(params: { skip?: number; limit?: number; keyword?: string }) {
  return http.get("/v1/certificates/records", { params });
}

export function issueCertRecord(body: {
  exam_service_record_id: number;
  cert_template_id: number;
  require_passed?: boolean;
}) {
  return http.post("/v1/certificates/records/issue", body);
}
