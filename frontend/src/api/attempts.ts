import { http } from "./http";

export function getAttempt(id: number) {
  return http.get(`/v1/attempts/${id}`);
}

export function saveAnswers(id: number, answers: { question_id: number; user_answer_json: unknown }[]) {
  return http.put(`/v1/attempts/${id}/answers`, { answers });
}

export function stageAnswers(id: number, answers: { question_id: number; user_answer_json: unknown }[]) {
  return http.post(`/v1/attempts/${id}/stage`, { answers });
}

export function restartPracticeAttempt(id: number) {
  return http.post(`/v1/attempts/${id}/restart-practice`);
}

export function submitAttempt(id: number) {
  return http.post(`/v1/attempts/${id}/submit`);
}
