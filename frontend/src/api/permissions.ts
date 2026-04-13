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

/** 功能模块聚合：菜单、列表/表单及所含字段、操作 */
export type AuthModulePayload = {
  moduleKey: string;
  moduleTitle: string;
  moduleCode?: string | null;
  menus: CatalogItem[];
  lists: { item: CatalogItem; fields: CatalogItem[] }[];
  forms: { item: CatalogItem; fields: CatalogItem[] }[];
  actions: CatalogItem[];
};

export function fetchPermissionCatalog() {
  return http.get<{
    groups: { label: string; items: CatalogItem[] }[];
    byKind: CatalogByKindLayer[];
    treeMlf: CatalogMlfModule[];
    fieldGroups: { label: string; items: CatalogItem[] }[];
    actionGroups: { label: string; items: CatalogItem[] }[];
    authModules: AuthModulePayload[];
  }>("/v1/permissions/catalog");
}
