import { createRouter, createWebHashHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { ElMessage } from "element-plus";

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
          path: "system/roles/:roleId/permissions",
          name: "role-permissions",
          component: () => import("@/views/system/RolePermissionPage.vue"),
          meta: { permission: "action.role.permission", title: "功能授权", keepAlive: true },
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
          meta: { permission: "menu.exam.question_manage" },
        },
        {
          path: "papers/publish",
          name: "papers-publish",
          component: () => import("@/views/papers/PaperPublish.vue"),
          meta: { permission: "menu.exam.paper_publish" },
        },
        {
          path: "papers",
          name: "papers",
          component: () => import("@/views/papers/PaperList.vue"),
          meta: { permission: "menu.exam.paper_manage" },
        },
        {
          path: "papers/:id",
          name: "paper-detail",
          component: () => import("@/views/papers/PaperDetail.vue"),
          meta: { permission: "menu.exam.paper_manage" },
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
          meta: { permission: "menu.exam.available", title: "在线考试" },
        },
        {
          path: "exam/candidate-manage",
          name: "exam-candidate-manage",
          component: () => import("@/views/exam/ExamCandidateList.vue"),
          meta: { permission: "menu.exam.candidate_manage", title: "考生管理" },
        },
        {
          path: "exam/services",
          name: "exam-services",
          component: () => import("@/views/exam/ExamServiceList.vue"),
          meta: { permission: "list.exam_service_record", title: "考试服务" },
        },
        {
          path: "exam/wrong-practice",
          name: "wrong-practice-list",
          component: () => import("@/views/exam/WrongPracticeList.vue"),
          meta: { permission: "list.wrong_practice", title: "错题练习" },
        },
        {
          path: "exam/wrong-practice/:courseId",
          name: "wrong-practice-take",
          component: () => import("@/views/exam/WrongPracticeTake.vue"),
          meta: { permission: "action.wrong_practice.enter", title: "错题练习" },
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
          component: () => import("@/views/system/CourseList.vue"),
          meta: { permission: "menu.system.course", title: "课程信息" },
        },
        {
          path: "system/paper-level/new",
          name: "paper-level-new",
          component: () => import("@/views/system/PaperLevelForm.vue"),
          meta: { permission: "menu.system.paper_level", title: "新建试卷等级" },
        },
        {
          path: "system/paper-level/:id/edit",
          name: "paper-level-edit",
          component: () => import("@/views/system/PaperLevelForm.vue"),
          meta: { permission: "menu.system.paper_level", title: "编辑试卷等级" },
        },
        {
          path: "system/paper-level",
          name: "system-paper-level",
          component: () => import("@/views/system/PaperLevelList.vue"),
          meta: { permission: "menu.system.paper_level", title: "试卷等级" },
        },
        {
          path: "system/students",
          name: "system-students",
          component: () => import("@/views/system/StudentList.vue"),
          meta: { permission: "menu.system.student", title: "学员管理" },
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
          component: () => import("@/views/system/PrintSettingsList.vue"),
          meta: {
            permission: ["menu.system.print", "list.print_template"],
            title: "打印设置",
          },
        },
        {
          path: "system/print-template/:id/design",
          name: "print-template-design",
          component: () => import("@/views/system/PrintTemplateDesign.vue"),
          meta: {
            permission: ["menu.system.print", "action.print_template.manage"],
            title: "模板设计",
          },
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
  // 正式考试锁定：禁止离开答题页（允许跳转到答卷详情页）
  const lock = localStorage.getItem("formal_exam_lock") || "";
  if (lock) {
    const isAttemptDetail = typeof to.path === "string" && /^\/attempts\/\d+$/.test(to.path);
    const isTakeExam = typeof to.path === "string" && to.path.startsWith("/exam/take/");
    if (!isAttemptDetail && !isTakeExam) {
      ElMessage.warning("正式考试进行中，禁止离开答题页面");
      return false;
    }
  }
  return true;
});

export default router;
