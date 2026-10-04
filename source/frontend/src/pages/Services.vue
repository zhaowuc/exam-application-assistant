<script setup>
import { ref, onMounted } from "vue";
import { get, post, act, query } from "../api";
import { zh, date } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
import Modal from "../components/Modal.vue";
const rows = ref([]),
  requests = ref([]),
  category = ref(""),
  search = ref(""),
  selected = ref(null),
  ask = ref(false),
  subject = ref(""),
  content = ref(""),
  loading = ref(true),
  error = ref(""),
  busy = ref(false);
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [a, b] = await Promise.all([
      get(
        `services/?${query({ category: category.value, search: search.value, page_size: 100 })}`,
      ),
      get("service-requests/?page_size=100"),
    ]);
    rows.value = a.results;
    requests.value = b.results;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
async function send() {
  busy.value = true;
  const result = await act(
    () =>
      post("service-requests/", {
        subject: subject.value,
        content: content.value,
        resource: selected.value?.id || null,
      }),
    "咨询已提交给本机管理员",
  );
  if (result) {
    ask.value = false;
    subject.value = "";
    content.value = "";
    load();
  }
  busy.value = false;
}
onMounted(load);
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">HELP, WHEN YOU NEED IT</div>
        <h1>公共服务</h1>
        <p>办事指南、材料清单与咨询服务，让准备更有条理。</p>
      </div>
      <button
        class="button primary"
        @click="
          ask = true;
          selected = null;
        "
      >
        <Icon name="message" :size="18" />提交咨询
      </button>
    </div>
    <section class="service-banner">
      <span class="service-banner-icon"
        ><Icon name="services" :size="38"
      /></span>
      <div>
        <h2>你的报考服务，集中在这里。</h2>
        <p>指南支持离线阅读；咨询由本机管理员处理。官方入口需联网访问。</p>
      </div>
    </section>
    <form class="filter-bar" @submit.prevent="load">
      <div class="search-input">
        <Icon name="search" :size="18" /><input
          v-model="search"
          placeholder="搜索服务与指南"
          aria-label="搜索公共服务"
        />
      </div>
      <select v-model="category" aria-label="服务分类" @change="load">
        <option value="">全部服务</option>
        <option
          v-for="key in ['guide', 'faq', 'materials', 'portal']"
          :key="key"
          :value="key"
        >
          {{ zh(key) }}
        </option></select
      ><button class="button">查找</button>
    </form>
    <States
      :loading="loading"
      :error="error"
      :empty="!rows.length"
      @retry="load"
    />
    <div v-if="!loading && !error" class="service-grid">
      <button
        v-for="row in rows"
        :key="row.id"
        class="service-card"
        @click="selected = row"
      >
        <span class="service-card-icon"
          ><Icon
            :name="
              row.category === 'faq'
                ? 'message'
                : row.category === 'portal'
                  ? 'external'
                  : 'file'
            "
            :size="25" /></span
        ><span class="pill subtle">{{ zh(row.category) }}</span>
        <h3>{{ row.title }}</h3>
        <p>{{ row.summary }}</p>
        <span class="text-link">查看服务 <Icon name="arrow" :size="16" /></span>
      </button>
    </div>
    <section class="card section">
      <div class="section-heading">
        <div>
          <h2>我的服务咨询</h2>
          <p>处理状态与管理员回复会保存在本机。</p>
        </div>
        <button class="icon-button" aria-label="刷新咨询" @click="load">
          <Icon name="refresh" :size="18" />
        </button>
      </div>
      <div v-for="request in requests" :key="request.id" class="request-item">
        <div class="between">
          <h3>{{ request.subject }}</h3>
          <span class="pill" :class="request.status">{{
            zh(request.status)
          }}</span>
        </div>
        <p class="prose">{{ request.content }}</p>
        <div v-if="request.response" class="reply-box">
          <strong>管理员回复</strong>
          <p class="prose">{{ request.response }}</p>
        </div>
        <small class="muted">提交于 {{ date(request.created_at) }}</small>
      </div>
      <div v-if="!requests.length" class="empty compact">
        <Icon name="message" :size="30" />
        <p>有问题？提交你的第一条咨询。</p>
      </div>
    </section>
    <Modal
      v-if="selected && !ask"
      :title="selected.title"
      @close="selected = null"
      ><span class="pill">{{ zh(selected.category) }}</span>
      <div class="prose service-content">{{ selected.content }}</div>
      <p v-if="selected.contact">联系方式：{{ selected.contact }}</p>
      <a
        v-if="selected.url"
        class="button"
        :href="selected.url"
        target="_blank"
        rel="noopener noreferrer"
        >打开官方入口（需要网络）<Icon name="external" :size="16" /></a
      ><button
        class="button primary"
        @click="
          subject = selected.title;
          ask = true;
        "
      >
        咨询这个服务
      </button></Modal
    ><Modal
      v-if="ask"
      title="提交服务咨询"
      @close="
        ask = false;
        selected = null;
      "
      ><p class="callout">
        本咨询由本机管理员回复，不发送给官方机构。请勿填写身份证号等敏感信息。
      </p>
      <form class="form-stack" @submit.prevent="send">
        <label
          >咨询主题<input v-model="subject" required maxlength="180" /></label
        ><label
          >问题描述<textarea
            v-model="content"
            required
            rows="5"
            maxlength="10000"
          /></label
        ><button class="button primary" :disabled="busy">
          {{ busy ? "正在提交…" : "提交咨询" }}
        </button>
      </form></Modal
    >
  </div>
</template>
