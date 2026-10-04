<script setup>
import { computed, ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { session, ui, get, post, saveSession, act } from "./api";
import Icon from "./components/Icon.vue";
import DemoGuide from "./components/DemoGuide.vue";
const route = useRoute(),
  router = useRouter(),
  open = ref(false);
const main = [
  ["/", "home", "今日概览"],
  ["/catalog/civil", "civil", "公务员报考"],
  ["/catalog/institution", "institution", "事业单位"],
  ["/catalog/graduate", "graduate", "研究生报考"],
  ["/services", "services", "公共服务"],
  ["/notices", "file", "公告资讯"],
];
const personal = [
  ["/recommendations", "layers", "智能推荐"],
  ["/favorites", "favorites", "收藏与比较"],
  ["/applications", "applications", "我的报考"],
  ["/practice", "practice", "在线刷题"],
  ["/scores", "scores", "学习报告"],
  ["/notifications", "notifications", "消息中心"],
];
const admin = [
  ["/admin", "admin", "管理总览"],
  ["/admin/applications", "applications", "报考数据管理"],
  ["/admin/opportunities", "civil", "招考信息管理"],
  ["/admin/services", "services", "公共服务管理"],
  ["/admin/service-requests", "message", "咨询回复"],
  ["/admin/users", "profile", "用户权限"],
  ["/admin/questions", "practice", "题库管理"],
  ["/admin/papers", "file", "试卷管理"],
  ["/admin/notifications", "notifications", "通知管理"],
  ["/admin/operations", "settings", "系统运行"],
];
const sections = computed(() => [
  { label: "发现", items: main },
  { label: "我的备考", items: personal },
  ...(session.user?.role === "admin"
    ? [{ label: "管理空间", items: admin }]
    : []),
]);
const title = computed(
  () =>
    [...main, ...personal, ...admin].find((x) => x[0] === route.path)?.[2] ||
    route.meta.title,
);
watch(
  () => route.path,
  () => {
    open.value = false;
  },
);
onMounted(async () => {
  if (session.user)
    try {
      session.user = await get("auth/me/");
    } catch {
      saveSession({ access: "", refresh: "", user: null });
      router.replace("/login");
    }
});
async function logout() {
  await act(() => post("auth/logout/", {}));
  saveSession({ access: "", refresh: "", user: null });
  router.push("/login");
}
</script>
<template>
  <div v-if="route.path === '/login'"><RouterView /></div>
  <div v-else class="app-shell">
    <div v-if="open" class="sidebar-shade" @click="open = false" />
    <aside class="sidebar" :class="{ open }">
      <RouterLink to="/" class="brand"
        ><span class="brand-mark"><Icon name="brand" :size="26" /></span
        ><span>报考小助手<small>EXAM ASSISTANT</small></span></RouterLink
      >
      <nav aria-label="主导航">
        <section v-for="group in sections" :key="group.label">
          <p class="nav-label">{{ group.label }}</p>
          <RouterLink
            v-for="[path, icon, label] in group.items"
            :key="path"
            :to="path"
            class="nav-link"
            :class="{ active: route.path === path }"
            ><Icon :name="icon" /><span>{{ label }}</span
            ><span v-if="path === '/services'" class="new-dot"
          /></RouterLink>
        </section>
      </nav>
      <div class="sidebar-bottom">
        <span class="status-dot" /> 离线工作台 <span>v2.0</span>
      </div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <div class="topbar-title">
          <button
            class="icon-button mobile-menu"
            aria-label="打开导航"
            @click="open = !open"
          >
            <Icon name="menu" /></button
          ><span>{{ title }}</span
          ><span class="divider" /><span class="muted topbar-sub"
            >为下一步，做好准备</span
          >
        </div>
        <div class="topbar-actions">
          <RouterLink
            to="/notifications"
            class="icon-button"
            aria-label="消息中心"
            ><Icon name="notifications" /></RouterLink
          ><RouterLink to="/profile" class="account"
            ><span class="avatar">{{
              session.user?.username?.[0]?.toUpperCase()
            }}</span
            ><span
              >{{ session.user?.username
              }}<small>{{
                session.user?.role === "admin" ? "管理员" : "个人空间"
              }}</small></span
            ></RouterLink
          ><button class="icon-button" aria-label="退出登录" @click="logout">
            <Icon name="logout" :size="18" />
          </button>
        </div>
      </header>
      <main id="main-content" class="main">
        <RouterView v-slot="{ Component }"
          ><Transition name="page" mode="out-in"
            ><component :is="Component" :key="route.path" /></Transition
        ></RouterView>
      </main>
      <footer class="app-footer">
        报考小助手 · 数据保存在本机<span>本地样本不代替官方公告与报名</span>
      </footer>
    </div>
  </div>
  <Transition name="fade"
    ><div
      v-if="ui.busy"
      class="load-indicator"
      role="status"
      aria-label="正在处理请求"
    >
      <span /></div
  ></Transition>
  <DemoGuide v-if="session.user && route.path !== '/login'" />
  <div class="toast-stack" aria-live="polite" aria-atomic="false">
    <TransitionGroup name="toast"
      ><div v-for="t in ui.toasts" :key="t.id" class="toast" :class="t.type">
        <Icon :name="t.type === 'error' ? 'alert' : 'success'" /><span>{{
          t.message
        }}</span
        ><button
          @click="ui.toasts = ui.toasts.filter((x) => x.id !== t.id)"
          aria-label="关闭提示"
        >
          <Icon name="close" :size="16" />
        </button></div
    ></TransitionGroup>
  </div>
</template>
