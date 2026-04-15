import { http } from "./http";

export function listExamCandidates(params: Record<string, unknown>) {
  return http.get("/v1/exam-candidates", { params });
}

export function createExamCandidate(body: Record<string, unknown>) {
  return http.post("/v1/exam-candidates", body);
}

export function patchExamCandidate(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/exam-candidates/${id}`, body);
}

export function deleteExamCandidate(id: number) {
  return http.delete(`/v1/exam-candidates/${id}`);
}

export function fetchExamCandidateStudentChoices(params: { enterprise_id?: number; keyword?: string; limit?: number }) {
  return http.get("/v1/exam-candidates/student-choices", { params });
}

export function downloadExamCandidateAttemptPdf(id: number) {
  return http.get(`/v1/exam-candidates/${id}/attempt-pdf`, { responseType: "blob" });
}

export function getExamCandidateAttemptReport(id: number) {
  return http.get(`/v1/exam-candidates/${id}/attempt-report`);
}
