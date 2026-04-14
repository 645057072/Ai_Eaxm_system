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

export function createPapersBatch(body: Record<string, unknown>) {
  return http.post("/v1/papers/batch", body);
}

export function updatePaper(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/papers/${id}`, body);
}

export function deletePaper(id: number) {
  return http.delete(`/v1/papers/${id}`);
}

/** 反组卷：清空试卷全部题目（场次引用中的试卷会409） */
export function clearPaperItems(paperId: number) {
  return http.delete(`/v1/papers/${paperId}/items`);
}

export function addPaperItem(paperId: number, body: Record<string, unknown>) {
  return http.post(`/v1/papers/${paperId}/items`, body);
}

export function removePaperItem(paperId: number, itemId: number) {
  return http.delete(`/v1/papers/${paperId}/items/${itemId}`);
}
