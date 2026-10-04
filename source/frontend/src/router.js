import { createRouter, createWebHistory } from "vue-router";
import { session } from "./api";
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      component: () => import("./pages/Login.vue"),
      meta: { public: true, title: "登录" },
    },
    {
      path: "/",
      component: () => import("./pages/Dashboard.vue"),
      meta: { title: "今日概览" },
    },
    {
      path: "/catalog/:type",
      component: () => import("./pages/Catalog.vue"),
      meta: { title: "招考查询" },
    },
    {
      path: "/opportunities/:id",
      component: () => import("./pages/Opportunity.vue"),
      meta: { title: "目标详情" },
    },
    {
      path: "/services",
      component: () => import("./pages/Services.vue"),
      meta: { title: "公共服务" },
    },
    {
      path: "/notices",
      component: () => import("./pages/Notices.vue"),
      meta: { title: "公告资讯" },
    },
    {
      path: "/recommendations",
      component: () => import("./pages/Recommendations.vue"),
      meta: { title: "智能推荐" },
    },
    {
      path: "/applications",
      component: () => import("./pages/Applications.vue"),
      meta: { title: "我的报考" },
    },
    {
      path: "/favorites",
      component: () => import("./pages/Favorites.vue"),
      meta: { title: "收藏与比较" },
    },
    {
      path: "/practice",
      component: () => import("./pages/Practice.vue"),
      meta: { title: "在线刷题" },
    },
    {
      path: "/exam/:id",
      component: () => import("./pages/Exam.vue"),
      meta: { title: "在线考试" },
    },
    {
      path: "/scores",
      component: () => import("./pages/Scores.vue"),
      meta: { title: "学习报告" },
    },
    {
      path: "/notifications",
      component: () => import("./pages/Notifications.vue"),
      meta: { title: "消息中心" },
    },
    {
      path: "/profile",
      component: () => import("./pages/Profile.vue"),
      meta: { title: "个人中心" },
    },
    {
      path: "/admin",
      component: () => import("./pages/Admin.vue"),
      meta: { admin: true, title: "管理总览" },
    },
    {
      path: "/admin/operations",
      component: () => import("./pages/Operations.vue"),
      meta: { admin: true, title: "系统运行" },
    },
    {
      path: "/admin/:resource",
      component: () => import("./pages/AdminResource.vue"),
      meta: { admin: true, title: "数据管理" },
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
  scrollBehavior: () => ({ top: 0 }),
});
router.beforeEach((to) => {
  if (!to.meta.public && !session.user)
    return { path: "/login", query: { next: to.fullPath } };
  if (to.meta.admin && session.user?.role !== "admin") return "/";
  document.title = `${to.meta.title || "工作台"} · 报考小助手`;
});
window.addEventListener("session-expired", () => router.replace("/login"));
export default router;
