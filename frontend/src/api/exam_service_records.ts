import { http } from "./http";

export function listExamServiceRecords(params: { skip?: number; limit?: number; keyword?: string }) {
  return http.get("/v1/exam-service-records", { params });
}
