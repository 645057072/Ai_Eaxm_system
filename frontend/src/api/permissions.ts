import { http } from "./http";

export type CatalogItem = { code: string; name: string; label: string; kind: string };

export type CatalogByKindLayer = {
  kind: string;
  title: string;
  sections: { label: string; items: CatalogItem[] }[];
};

export type CatalogMlfGroup = {
  name: string;
  menus: CatalogItem[];
  lists: CatalogItem[];
  forms: CatalogItem[];
};

export type CatalogMlfModule = {
  module: string;
  groups: CatalogMlfGroup[];
};

export function fetchPermissionCatalog() {
  return http.get<{
    groups: { label: string; items: CatalogItem[] }[];
    byKind: CatalogByKindLayer[];
    treeMlf: CatalogMlfModule[];
    fieldGroups: { label: string; items: CatalogItem[] }[];
    actionGroups: { label: string; items: CatalogItem[] }[];
  }>("/v1/permissions/catalog");
}
