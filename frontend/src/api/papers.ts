import { http } from "./http";

export function listPapers(params: Record<string, unknown>) {
  return http.get("/v1/papers", { params });
}

export function getPaper(id: number) {
  return http.get(`/v1/papers/${id}`);
}

export function createPaper(body: Record<string, unknown>) {
  return http.post("/v1/papers", body);
}

export function updatePaper(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/papers/${id}`, body);
}

export function deletePaper(id: number) {
  return http.delete(`/v1/papers/${id}`);
}

export function addPaperItem(paperId: number, body: Record<string, unknown>) {
  return http.post(`/v1/papers/${paperId}/items`, body);
}

export function removePaperItem(paperId: number, itemId: number) {
  return http.delete(`/v1/papers/${paperId}/items/${itemId}`);
}
