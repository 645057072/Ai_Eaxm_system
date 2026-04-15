import { http } from "./http";

export function listWrongPracticeCourses(params: { skip?: number; limit?: number; keyword?: string }) {
  return http.get("/v1/wrong-practice", { params });
}

export function getNextWrongQuestion(courseId: number) {
  return http.get(`/v1/wrong-practice/${courseId}/next`);
}

export function submitWrongAnswer(courseId: number, body: { question_id: number; user_answer_json: unknown }) {
  return http.post(`/v1/wrong-practice/${courseId}/submit`, body);
}

