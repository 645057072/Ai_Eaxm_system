import { http } from "./http";

export function listRoles() {
  return http.get("/v1/roles");
}
