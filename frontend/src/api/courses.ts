import { http } from "./http";

export function listCourses(params: {
  skip?: number;
  limit?: number;
  keyword?: string;
  enterprise_id?: number;
}) {
  return http.get("/v1/courses", { params });
}

export function createCourse(body: Record<string, unknown>) {
  return http.post("/v1/courses", body);
}

export function patchCourse(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/courses/${id}`, body);
}

export function deleteCourse(id: number) {
  return http.delete(`/v1/courses/${id}`);
}
