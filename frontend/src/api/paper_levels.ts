import { http } from "./http";

export function listPaperLevels(params: Record<string, unknown>) {
  return http.get("/v1/paper-levels", { params });
}

export function getPaperLevel(id: number) {
  return http.get(`/v1/paper-levels/${id}`);
}

export function createPaperLevel(body: Record<string, unknown>) {
  return http.post("/v1/paper-levels", body);
}

export function patchPaperLevel(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/paper-levels/${id}`, body);
}

export function deletePaperLevel(id: number) {
  return http.delete(`/v1/paper-levels/${id}`);
}
