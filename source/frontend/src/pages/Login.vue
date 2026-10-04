<script setup>
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { post, saveSession } from "../api";
import Icon from "../components/Icon.vue";
const router = useRouter(),
  route = useRoute(),
  registering = ref(false),
  busy = ref(false),
  error = ref("");
const username = ref(""),
  password = ref(""),
  email = ref(""),
  showPassword = ref(false);
function demo(role) {
  username.value = role;
  password.value = role === "admin" ? "Admin@123456" : "Demo@123456";
  error.value = "";
}
async function submit() {
  busy.value = true;
  error.value = "";
  try {
    const value = await post(
      `auth/${registering.value ? "register" : "login"}/`,
      {
        username: username.value,
        password: password.value,
        ...(registering.value ? { email: email.value } : {}),
      },
    );
    saveSession(value);
    router.replace(
      route.query.next?.startsWith("/") && !route.query.next.startsWith("//")
        ? route.query.next
        : "/",
    );
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <main class="login-page">
    <div class="login-atmosphere" aria-hidden="true">
      <div class="orb orb-a" />
      <div class="orb orb-b" />
      <div class="orb orb-c" />
      <div class="orbit orbit-a" />
      <div class="orbit orbit-b" />
      <div class="grain" />
    </div>
    <header class="login-header">
      <span class="brand"
        ><span class="brand-mark"><Icon name="brand" :size="27" /></span
        ><span>报考小助手<small>EXAM ASSISTANT</small></span></span
      ><span class="login-offline"
        ><span class="status-dot" /> OFFLINE EDITION</span
      >
    </header>
    <div class="login-layout">
      <section class="login-story">
        <div class="eyebrow light"><span />为理想，有序前行</div>
        <h1>让每一次选择，<br />更接近<span>你的未来。</span></h1>
        <p>发现适合你的报考方向。<br />从目标筛选，到每一天的认真准备。</p>
        <div class="story-features">
          <div>
            <Icon name="layers" /><span
              >看清方向<small>资格匹配与智能推荐</small></span
            >
          </div>
          <div>
            <Icon name="practice" /><span
              >稳步进阶<small>本地题库与学习分析</small></span
            >
          </div>
          <div>
            <Icon name="admin" /><span
              >安心备考<small>离线可用，数据留在本机</small></span
            >
          </div>
        </div>
        <div class="story-note">
          <span class="tiny-line" />少一点不确定，多一点从容。
        </div>
      </section>
      <section class="login-card">
        <div class="login-card-top">
          <span class="login-card-symbol"><Icon name="brand" :size="30" /></span
          ><span>YOUR NEXT CHAPTER</span>
        </div>
        <h2>{{ registering ? "开启你的备考旅程" : "欢迎回来" }}</h2>
        <p class="muted">
          {{
            registering
              ? "创建本机账号，保存你的每一步进展"
              : "登录工作台，继续你的下一步"
          }}
        </p>
        <form @submit.prevent="submit">
          <label
            >用户名<input
              v-model="username"
              autocomplete="username"
              required
              maxlength="150"
              placeholder="请输入用户名" /></label
          ><label v-if="registering"
            >电子邮箱<input
              v-model="email"
              type="email"
              autocomplete="email"
              placeholder="选填，用于个人资料" /></label
          ><label
            >密码
            <div class="password-field">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                :autocomplete="
                  registering ? 'new-password' : 'current-password'
                "
                required
                minlength="8"
                placeholder="请输入密码"
              /><button
                type="button"
                @click="showPassword = !showPassword"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              >
                {{ showPassword ? "隐藏" : "显示" }}
              </button>
            </div></label
          >
          <div v-if="error" class="form-error" role="alert">
            <Icon name="alert" :size="17" />{{ error }}
          </div>
          <button class="button primary login-submit" :disabled="busy">
            <Icon v-if="busy" name="loading" class="spin" :size="18" /><span>{{
              busy ? "正在开启工作台…" : registering ? "创建账号" : "登录工作台"
            }}</span
            ><Icon v-if="!busy" name="arrow" :size="18" />
          </button>
        </form>
        <p class="login-switch">
          {{ registering ? "已有账号？" : "还没有账号？"
          }}<button
            @click="
              registering = !registering;
              error = '';
            "
          >
            {{ registering ? "返回登录" : "创建本机账号" }}
          </button>
        </p>
        <div v-if="!registering" class="demo-box">
          <span>本地体验账号 · 首次使用可直接体验</span>
          <div>
            <button @click="demo('demo')">
              普通用户 <Icon name="arrow" :size="14" /></button
            ><button @click="demo('admin')">
              管理员 <Icon name="arrow" :size="14" />
            </button>
          </div>
          <small>正式使用前，请修改默认密码。</small>
        </div>
        <div class="login-privacy">
          <Icon name="admin" :size="15" />无需云端连接 · 资料仅存储在本机
        </div>
      </section>
    </div>
    <footer class="login-footer">
      <span>报考小助手 / 离线重构版 2.0</span
      ><span>发现 · 比较 · 准备 · 前行</span>
    </footer>
  </main>
</template>
