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
          name: "users",
          component: () => import("@/views/users/UserList.vue"),
          meta: { roles: ["admin"] },
        },
        {
          path: "questions",
          name: "questions",
          component: () => import("@/views/questions/QuestionList.vue"),
          meta: { roles: ["admin", "teacher"] },
        },
        {
          path: "papers",
          name: "papers",
          component: () => import("@/views/papers/PaperList.vue"),
          meta: { roles: ["admin", "teacher"] },
        },
        {
          path: "papers/:id",
          name: "paper-detail",
          component: () => import("@/views/papers/PaperDetail.vue"),
          meta: { roles: ["admin", "teacher"] },
        },
        {
          path: "sessions",
          name: "sessions",
          component: () => import("@/views/sessions/SessionList.vue"),
          meta: { roles: ["admin", "teacher"] },
        },
        {
          path: "exam/available",
          name: "exam-available",
          component: () => import("@/views/exam/AvailableExams.vue"),
          meta: { roles: ["student"] },
        },
        {
          path: "exam/take/:sessionId",
          name: "exam-take",
          component: () => import("@/views/exam/TakeExam.vue"),
          meta: { roles: ["student"] },
        },
        {
          path: "attempts/:id",
          name: "attempt-detail",
          component: () => import("@/views/exam/AttemptDetail.vue"),
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
  const roles = to.meta.roles as string[] | undefined;
  if (roles && roles.length && auth.roleCode && !roles.includes(auth.roleCode)) {
    return { name: "home" };
  }
  return true;
});

export default router;
