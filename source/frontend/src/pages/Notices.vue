<script setup>
import { ref, onMounted } from "vue";
import { get, query } from "../api";
import { zh, date } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
import Pagination from "../components/Pagination.vue";
import Modal from "../components/Modal.vue";
const rows = ref([]),
  page = ref(1),
  count = ref(0),
  search = ref(""),
  type = ref(""),
  selected = ref(null),
  loading = ref(true),
  error = ref("");
async function load(p = 1) {
  page.value = p;
  loading.value = true;
  error.value = "";
  try {
    const data = await get(
      `notices/?${query({ page: p, search: search.value, exam_type: type.value })}`,
    );
    rows.value = data.results;
    count.value = data.count;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">STAY INFORMED</div>
        <h1>公告资讯</h1>
        <p>阅读本地公告，留意报名和考试提醒。</p>
      </div>
    </div>
    <form class="filter-bar" @submit.prevent="load()">
      <div class="search-input">
        <Icon name="search" :size="18" /><input
          v-model="search"
          aria-label="搜索公告"
          placeholder="搜索公告标题与内容"
        />
      </div>
      <select v-model="type" aria-label="考试类型" @change="load()">
        <option value="">全部类型</option>
        <option
          v-for="t in ['civil', 'institution', 'graduate', 'all']"
          :key="t"
          :value="t"
        >
          {{ zh(t) }}
        </option></select
      ><button class="button">查询</button>
    </form>
    <States
      :loading="loading"
      :error="error"
      :empty="!rows.length"
      @retry="load(page)"
    />
    <div class="notice-list" v-if="!loading && !error">
      <button
        v-for="row in rows"
        :key="row.id"
        class="card notice-card"
        @click="selected = row"
      >
        <div class="tag-row">
          <span>{{ zh(row.exam_type) }}</span
          ><span v-if="row.is_featured">重要公告</span
          ><span v-if="row.is_demo">演示</span>
        </div>
        <h2>{{ row.title }}</h2>
        <p>{{ row.summary || row.content.slice(0, 110) }}</p>
        <small
          >{{ row.publisher || row.source }} ·
          {{ date(row.published_at) }}</small
        ><Icon name="up" :size="19" />
      </button>
    </div>
    <Pagination :page="page" :count="count" @change="load" /><Modal
      v-if="selected"
      :title="selected.title"
      wide
      @close="selected = null"
      ><p class="muted">
        {{ selected.publisher }} · {{ date(selected.published_at) }}
      </p>
      <div class="prose">{{ selected.content }}</div>
      <p class="data-note">来源：{{ selected.source }}</p>
      <a
        v-if="selected.source_url"
        :href="selected.source_url"
        target="_blank"
        rel="noopener noreferrer"
        class="button"
        >查看原文（联网）<Icon name="external" :size="16" /></a
    ></Modal>
  </div>
</template>
