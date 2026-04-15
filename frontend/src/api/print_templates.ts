import { http } from "./http";

export function listPrintTemplates(params: Record<string, unknown>) {
  return http.get("/v1/print-templates", { params });
}

export function getPrintTemplate(id: number) {
  return http.get(`/v1/print-templates/${id}`);
}

export function resolvePrintTemplate(courseId: number) {
  return http.get("/v1/print-templates/resolve", { params: { course_id: courseId } });
}

export function createPrintTemplate(body: Record<string, unknown>) {
  return http.post("/v1/print-templates", body);
}

export function updatePrintTemplate(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/print-templates/${id}`, body);
}

export function resetPrintTemplate(id: number) {
  return http.post(`/v1/print-templates/${id}/reset`);
}

export function publishPrintTemplate(id: number, body: { enterprise_id?: number | null }) {
  return http.post(`/v1/print-templates/${id}/publish`, body);
}

export function deletePrintTemplate(id: number) {
  return http.delete(`/v1/print-templates/${id}`);
}
