import { http } from "./http";

export function listStudents(params: Record<string, unknown>) {
  return http.get("/v1/students", { params });
}

export function createStudent(body: Record<string, unknown>) {
  return http.post("/v1/students", body);
}

export function patchStudent(id: number, body: Record<string, unknown>) {
  return http.patch(`/v1/students/${id}`, body);
}

export function deleteStudent(id: number) {
  return http.delete(`/v1/students/${id}`);
}

export function importStudents(fd: FormData) {
  return http.post("/v1/students/import", fd, { headers: { "Content-Type": "multipart/form-data" } });
}

