<script setup>
import { ref, onMounted } from "vue";
import { get, post, act } from "../api";
import { date } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
import Pagination from "../components/Pagination.vue";
const rows = ref([]),
  loading = ref(true),
  error = ref(""),
  page = ref(1),
  count = ref(0);
async function load(p = 1) {
  page.value = p;
  loading.value = true;
  error.value = "";
  try {
    const data = await get(`notifications/?page=${p}`);
    rows.value = data.results;
    count.value = data.count;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
async function read(row) {
  await act(() => post(`notifications/${row.id}/read/`, {}));
  row.is_read = true;
}
onMounted(load);
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">NOTHING IMPORTANT MISSED</div>
        <h1>消息中心</h1>
        <p>公告提醒、报考更新与咨询回复，集中查看。</p>
      </div>
      <button
        class="button"
        @click="
          act(
            () => post('notifications/read-all/', {}),
            '已全部标记为已读',
          ).then(() => load(page))
        "
      >
        <Icon name="done" :size="17" />全部已读
      </button>
    </div>
    <States
      :loading="loading"
      :error="error"
      :empty="!rows.length"
      text="暂时没有新消息"
      @retry="load(page)"
    />
    <div v-if="!loading && !error" class="notification-list">
      <article
        v-for="row in rows"
        :key="row.id"
        class="card notification-card"
        :class="{ unread: !row.is_read }"
      >
        <span class="notification-icon"
          ><Icon name="notifications" :size="22"
        /></span>
        <div>
          <div class="between">
            <h2>{{ row.title }}</h2>
            <span v-if="!row.is_read" class="pill">未读</span>
          </div>
          <p class="prose">{{ row.content }}</p>
          <small class="muted">{{ date(row.created_at) }}</small>
          <div class="notification-actions">
            <button v-if="!row.is_read" class="text-link" @click="read(row)">
              标记已读</button
            ><RouterLink
              v-if="row.link?.startsWith('/') && !row.link.startsWith('//')"
              :to="row.link"
              class="text-link"
              >查看详情 <Icon name="arrow" :size="15"
            /></RouterLink>
          </div>
        </div>
      </article>
    </div>
    <Pagination :page="page" :count="count" @change="load" />
  </div>
</template>
