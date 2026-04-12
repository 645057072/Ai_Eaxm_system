/// <reference types="vite/client" />

declare module "vue" {
  export interface GlobalComponents {
    AppEmoji: (typeof import("./components/AppEmoji.vue"))["default"];
  }
}

interface ImportMetaEnv {
  readonly VITE_API_BASE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
