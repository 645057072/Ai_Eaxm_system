import { http } from "./http";

export function listQuestions(params: Record<string, unknown>) {
  return http.get("/v1/questions", { params });
}

export function getQuestion(id: number) {
  return http.get(`/v1/questions/${id}`);
}

/** 与列表筛选一致时的上一题/下一题 id（排序与列表相同） */
export function getQuestionNeighbors(id: number, params?: Record<string, unknown>) {
  return http.get(`/v1/questions/${id}/neighbors`, { params });
}

export function createQuestion(body: Record<string, unknown>) {
  return http.post("/v1/questions", body);
}

export function updateQuestion(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/questions/${id}`, body);
}

export function deleteQuestion(id: number) {
  return http.delete(`/v1/questions/${id}`);
}

/** 批量发布：草稿改为已发布 */
export function batchPublishQuestions(ids: number[]) {
  return http.post("/v1/questions/batch-publish", { ids });
}

/** 导入题库（multipart：course_id、enterprise_id、file） */
export function importQuestions(formData: FormData) {
  return http.post("/v1/questions/import", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}
