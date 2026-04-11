import { http } from "./http";

export function listSessions(params: Record<string, unknown>) {
  return http.get("/v1/exam-sessions", { params });
}

export function createSession(body: Record<string, unknown>) {
  return http.post("/v1/exam-sessions", body);
}

export function updateSession(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/exam-sessions/${id}`, body);
}

export function publishSession(id: number) {
  return http.post(`/v1/exam-sessions/${id}/publish`);
}

export function listAvailable() {
  return http.get("/v1/exam-sessions/available/list", { params: { skip: 0, limit: 100 } });
}

export function getTakeData(sessionId: number) {
  return http.get(`/v1/exam-sessions/${sessionId}/take-data`);
}

export function startExam(sessionId: number) {
  return http.post(`/v1/exam-sessions/${sessionId}/start`);
}
