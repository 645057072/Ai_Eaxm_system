import { http } from "./http";

export function listQuestions(params: Record<string, unknown>) {
  return http.get("/v1/questions", { params });
}

export function getQuestion(id: number) {
  return http.get(`/v1/questions/${id}`);
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
