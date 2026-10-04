<script setup>
import { computed, ref, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import { session } from "../api";
import Icon from "./Icon.vue";
const router = useRouter(),
  visible = ref(false),
  step = ref(0),
  cinema = ref(false);
const steps = computed(() => [
  {
    path: "/",
    icon: "home",
    title: "01 · 认识离线工作台",
    text: "展示招考目标、题库与公共服务入口。所有页面资源都已包含在交付包中。",
  },
  {
    path: "/catalog/civil",
    icon: "civil",
    title: "02 · 找到合适的目标",
    text: "搜索岗位，打开详情，检查资格条件；可以收藏、比较并记录本地报考。",
  },
  {
    path: "/services",
    icon: "services",
    title: "03 · 新增公共服务",
    text: "打开办事指南、材料清单与常见问题；提交咨询后由本机管理员回复。",
  },
  {
    path: "/applications",
    icon: "applications",
    title: "04 · 记录报考与计划",
    text: "展示真实保存的报考记录与考试计划。这里不会代替官方报名。",
  },
  {
    path: "/practice",
    icon: "practice",
    title: "05 · 从练习到学习报告",
    text: "生成练习卷，选择答案并交卷。成绩、错题和薄弱分析会自动更新。",
  },
  ...(session.user?.role === "admin"
    ? [
        {
          path: "/admin/applications",
          icon: "admin",
          title: "06 · 新增报考数据管理",
          text: "审核用户的报考记录，填写审核说明、成绩和结果；支持筛选与导出。",
        },
        {
          path: "/admin/operations",
          icon: "settings",
          title: "07 · 展示离线交付能力",
          text: "创建数据库备份，查看运行状态。移动或交付时保留整个程序目录。",
        },
      ]
    : []),
]);
function navigate(i) {
  step.value = i;
  router.push(steps.value[i].path);
}
function toggle() {
  visible.value = !visible.value;
}
function key(e) {
  if (e.altKey && e.key.toLowerCase() === "d") {
    e.preventDefault();
    toggle();
  }
  if (e.key === "Escape" && visible.value) visible.value = false;
}
window.addEventListener("keydown", key);
onBeforeUnmount(() => {
  window.removeEventListener("keydown", key);
  document.documentElement.classList.remove("cinema-mode");
});
function setCinema() {
  cinema.value = !cinema.value;
  document.documentElement.classList.toggle("cinema-mode", cinema.value);
}
</script>
<template>
  <button
    class="demo-launch"
    @click="toggle"
    aria-label="打开演示导航"
    :aria-expanded="visible"
  >
    <Icon name="play" :size="16" /><span>演示导航</span><kbd>Alt D</kbd></button
  ><Transition name="demo"
    ><aside v-if="visible" class="demo-guide" aria-label="功能演示导航">
      <div class="demo-guide-header">
        <span><i /> LIVE PRODUCT TOUR</span
        ><button
          class="icon-button"
          @click="visible = false"
          aria-label="关闭演示导航"
        >
          <Icon name="close" :size="17" />
        </button>
      </div>
      <div class="demo-guide-progress">
        <button
          v-for="(item, i) in steps"
          :key="item.path"
          :class="{ current: step === i, visited: i < step }"
          @click="navigate(i)"
          :aria-label="item.title"
        />
      </div>
      <div class="demo-guide-body">
        <span class="demo-guide-symbol"
          ><Icon :name="steps[step].icon" :size="25"
        /></span>
        <h3>{{ steps[step].title }}</h3>
        <p>{{ steps[step].text }}</p>
      </div>
      <div class="demo-guide-footer">
        <button class="text-link" @click="setCinema">
          <Icon name="layers" :size="14" />{{
            cinema ? "退出聚焦展示" : "聚焦展示"
          }}
        </button>
        <div>
          <button
            class="icon-button"
            :disabled="step === 0"
            @click="navigate(step - 1)"
            aria-label="上一演示步骤"
          >
            <Icon name="left" :size="18" /></button
          ><button
            class="button primary small"
            @click="navigate(step === steps.length - 1 ? 0 : step + 1)"
          >
            {{ step === steps.length - 1 ? "回到开始" : "下一步"
            }}<Icon name="arrow" :size="14" />
          </button>
        </div>
      </div>
      <p class="demo-guide-note">只导航，不自动创建记录或修改数据。</p>
    </aside></Transition
  >
</template>
