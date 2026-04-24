import { http } from "./http";

export function listExamServiceRecords(params: {
  skip?: number;
  limit?: number;
  keyword?: string;
  passed?: boolean;
}) {
  return http.get("/v1/exam-service-records", { params });
}
