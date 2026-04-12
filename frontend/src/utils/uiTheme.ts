/** 预置界面主题 id，与 ui-themes.css 中 data-ui-theme 一致 */

export const UI_THEME_IDS = ["nebula", "aurora", "deepblue", "amber", "jade"] as const;

export type UiThemeId = (typeof UI_THEME_IDS)[number];

const STORAGE_KEY = "exam_ui_theme";

export function getStoredUiTheme(): UiThemeId {
  const v = localStorage.getItem(STORAGE_KEY);
  if (v && UI_THEME_IDS.includes(v as UiThemeId)) return v as UiThemeId;
  return "nebula";
}

export function applyUiTheme(id: UiThemeId) {
  document.documentElement.dataset.uiTheme = id;
  localStorage.setItem(STORAGE_KEY, id);
}
