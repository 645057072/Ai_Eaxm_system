/**
 * 系统级 Emoji 资源映射（仅在此文件维护图形字符；业务界面通过 AppEmoji 或工具函数引用）
 */
export const SYSTEM_EMOJI = {
  brand: "\u{1F393}",
  home: "\u{1F3E0}",
  users: "\u{1F465}",
  questionBank: "\u{1F4DA}",
  papers: "\u{1F4C4}",
  sessions: "\u{1F4C5}",
  availableExams: "\u{1F4DD}",
  login: "\u{1F510}",
  logout: "\u{1F6AA}",
  search: "\u{1F50D}",
  add: "\u2795",
  edit: "\u270F\uFE0F",
  delete: "\u{1F5D1}\uFE0F",
  compose: "\u{1F4CE}",
  publish: "\u{1F4E2}",
  enterExam: "\u{1F3AF}",
  user: "\u{1F464}",
  roleAdmin: "\u2699\uFE0F",
  roleTeacher: "\u{1F468}\u200D\u{1F3EB}",
  roleStudent: "\u{1F393}",
  enabledYes: "\u2705",
  enabledNo: "\u26AA",
  back: "\u2190",
  remove: "\u274C",
  addToPaper: "\u2795",
  save: "\u{1F4BE}",
  submitExam: "\u{1F4E4}",
  welcome: "\u{1F44B}",
  list: "\u{1F4CB}",
  /** 系统管理、数智 BI 等扩展菜单 */
  systemMgmt: "\u{1F6E0}\uFE0F",
  biCenter: "\u{1F4CA}",
  basicInfo: "\u{1F4C1}",
  settingsCenter: "\u2699\uFE0F",
  supervision: "\u{1F441}\uFE0F",
  enterprise: "\u{1F3E2}",
  course: "\u{1F4D2}",
  documentDesign: "\u{1F4DD}",
  printSettings: "\u{1F5BC}\uFE0F",
  onlineUsers: "\u{1F465}",
  logMgmt: "\u{1F4DC}",
  /** 用户管理子菜单 */
  userInfo: "\u{1F464}",
  rolePerm: "\u{1F512}",
} as const;

export type SystemEmojiKey = keyof typeof SYSTEM_EMOJI;

export function getSystemEmoji(key: SystemEmojiKey): string {
  return SYSTEM_EMOJI[key];
}

/** 按角色 code 选择列表中展示的 Emoji 键 */
export function systemEmojiRoleKey(code: string | undefined): SystemEmojiKey {
  if (code === "admin") return "roleAdmin";
  if (code === "teacher") return "roleTeacher";
  if (code === "student") return "roleStudent";
  return "user";
}
