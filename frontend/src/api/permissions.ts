import { http } from "./http";

export function fetchPermissionCatalog() {
  return http.get<{ groups: { label: string; items: { code: string; name: string; kind: string }[] }[] }>(
    "/v1/permissions/catalog",
  );
}
