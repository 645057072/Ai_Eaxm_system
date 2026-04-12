import { createRouter, createWebHashHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/LoginView.vue"),
      meta: { public: true },
    },
    {
      path: "/",
      component: () => import("@/layouts/MainLayout.vue"),
      meta: { requiresAuth: true },
      children: [
        {
          path: "",
          name: "home",
          component: () => import("@/views/HomeView.vue"),
        },
        {
          path: "users",
          redirect: "/system/users",
        },
        {
          path: "system/users",
          name: "system-users",
          component: () => import("@/views/users/UserList.vue"),
          meta: { permission: "menu.system.users" },
        },
        {
          path: "system/roles",
          name: "system-roles",
          component: () => import("@/views/system/RoleList.vue"),
          meta: { permission: "menu.system.roles" },
        },
        {
          path: "questions",
          name: "questions",
          component: () => import("@/views/questions/QuestionList.vue"),
          meta: { permission: "menu.exam.questions" },
        },
        {
          path: "papers",
          name: "papers",
          component: () => import("@/views/papers/PaperList.vue"),
          meta: { permission: "menu.exam.papers" },
        },
        {
          path: "papers/:id",
          name: "paper-detail",
          component: () => import("@/views/papers/PaperDetail.vue"),
          meta: { permission: "menu.exam.papers" },
        },
        {
          path: "sessions",
          name: "sessions",
          component: () => import("@/views/sessions/SessionList.vue"),
          meta: { permission: "menu.exam.sessions" },
        },
        {
          path: "exam/available",
          name: "exam-available",
          component: () => import("@/views/exam/AvailableExams.vue"),
          meta: { permission: "menu.exam.available" },
        },
        {
          path: "exam/take/:sessionId",
          name: "exam-take",
          component: () => import("@/views/exam/TakeExam.vue"),
          meta: { permission: "action.exam.take" },
        },
        {
          path: "attempts/:id",
          name: "attempt-detail",
          component: () => import("@/views/exam/AttemptDetail.vue"),
          meta: { permission: ["list.attempt", "action.exam.take"] },
        },
        {
          path: "system/enterprise",
          name: "system-enterprise",
          component: () => import("@/views/system/EnterpriseList.vue"),
          meta: { permission: "menu.system.enterprise", title: "企业信息" },
        },
        {
          path: "system/course",
          name: "system-course",
          component: () => import("@/views/placeholder/ModulePlaceholder.vue"),
          meta: { permission: "menu.system.course", title: "课程信息" },
        },
        {
          path: "system/document-design",
          name: "system-document-design",
          component: () => import("@/views/placeholder/ModulePlaceholder.vue"),
          meta: { permission: "menu.system.document", title: "单据设计" },
        },
        {
          path: "system/print-settings",
          name: "system-print-settings",
          component: () => import("@/views/placeholder/ModulePlaceholder.vue"),
          meta: { permission: "menu.system.print", title: "打印设置" },
        },
        {
          path: "system/online-users",
          name: "system-online-users",
          component: () => import("@/views/placeholder/ModulePlaceholder.vue"),
          meta: { permission: "menu.system.online", title: "在线用户" },
        },
        {
          path: "system/logs",
          name: "system-logs",
          component: () => import("@/views/placeholder/ModulePlaceholder.vue"),
          meta: { permission: "menu.system.logs", title: "日志管理" },
        },
        {
          path: "bi",
          name: "bi-center",
          component: () => import("@/views/placeholder/ModulePlaceholder.vue"),
          meta: { permission: "menu.bi", title: "数智BI中心" },
        },
      ],
    },
  ],
});

router.beforeEach(async (to) => {
  if (to.meta.public) return true;
  const auth = useAuthStore();
  if (!auth.token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (!auth.me) {
    try {
      await auth.loadMe();
    } catch {
      auth.logout();
      return { name: "login" };
    }
  }
  const perm = to.meta.permission as string | string[] | undefined;
  if (perm) {
    const codes = Array.isArray(perm) ? perm : [perm];
    if (!codes.some((c) => auth.can(c))) {
      return { name: "home" };
    }
  }
  return true;
});

export default router;
