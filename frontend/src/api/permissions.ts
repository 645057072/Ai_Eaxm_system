import { http } from "./http";

export type CatalogItem = { code: string; name: string; label: string; kind: string };

export type CatalogByKindLayer = {
  kind: string;
  title: string;
  sections: { label: string; items: CatalogItem[] }[];
};

export function fetchPermissionCatalog() {
  return http.get<{
    groups: { label: string; items: CatalogItem[] }[];
    byKind: CatalogByKindLayer[];
  }>("/v1/permissions/catalog");
}
