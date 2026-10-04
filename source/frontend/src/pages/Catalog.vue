<script setup>
import { ref, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { get, post, act, query } from "../api";
import { zh } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
import Pagination from "../components/Pagination.vue";
const route = useRoute(),
  rows = ref([]),
  page = ref(1),
  count = ref(0),
  loading = ref(true),
  error = ref(""),
  search = ref(""),
  region = ref(""),
  year = ref(""),
  home = ref({ regions: [], years: [] });
let generation = 0;
async function load(newPage = 1) {
  page.value = newPage;
  loading.value = true;
  error.value = "";
  const version = ++generation;
  try {
    const data = await get(
      `opportunities/?${query({ opportunity_type: route.params.type, search: search.value, region: region.value, year: year.value, page: newPage })}`,
    );
    if (version === generation) {
      rows.value = data.results;
      count.value = data.count;
    }
  } catch (e) {
    if (version === generation) error.value = e.message;
  } finally {
    if (version === generation) loading.value = false;
  }
}
onMounted(async () => {
  load();
  try {
    home.value = await get("home/");
  } catch {}
});
watch(
  () => route.params.type,
  () => {
    search.value = "";
    region.value = "";
    year.value = "";
    load();
  },
);
function favorite(id) {
  act(() => post("favorites/", { opportunity: id }), "已加入收藏");
}
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">EXPLORE YOUR POSSIBILITIES</div>
        <h1>{{ zh(route.params.type) }}报考</h1>
        <p>查看岗位与院校条件，用本地历史数据辅助你的选择。</p>
      </div>
      <span class="pill">{{ count }} 个报考目标</span>
    </div>
    <form class="filter-bar" @submit.prevent="load()">
      <div class="search-input">
        <Icon name="search" :size="18" /><input
          v-model="search"
          aria-label="搜索招考信息"
          placeholder="搜索岗位、单位、专业或编号"
        />
      </div>
      <select v-model="region" aria-label="地区" @change="load()">
        <option value="">全部地区</option>
        <option v-for="r in home.regions" :key="r">{{ r }}</option></select
      ><select v-model="year" aria-label="年份" @change="load()">
        <option value="">全部年份</option>
        <option v-for="y in home.years" :key="y" :value="y">
          {{ y }} 年
        </option></select
      ><button class="button primary">查询</button>
    </form>
    <States
      :loading="loading"
      :error="error"
      :empty="!rows.length"
      @retry="load(page)"
    />
    <div v-if="!loading && !error" class="opportunity-grid">
      <article v-for="row in rows" :key="row.id" class="opportunity-card">
        <div class="card-topline">
          <span class="type-icon" :class="row.opportunity_type"
            ><Icon :name="row.opportunity_type" :size="22" /></span
          ><span class="pill subtle">{{ row.region }} · {{ row.year }}</span>
        </div>
        <RouterLink
          :to="`/opportunities/${row.id}`"
          class="opportunity-title"
          >{{ row.title }}</RouterLink
        >
        <p class="organization">{{ row.organization }}</p>
        <div class="tag-row">
          <span>{{ row.education_required }}</span
          ><span>{{ row.slots }} 个名额</span
          ><span v-if="row.is_demo">演示数据</span>
        </div>
        <p class="requirement-text">{{ row.major_requirement }}</p>
        <div class="card-bottom">
          <span
            >历史竞争比
            <strong
              >{{ row.competition_ratio || "暂无"
              }}{{ row.competition_ratio ? ":1" : "" }}</strong
            ></span
          >
          <div>
            <button
              class="icon-button"
              @click="favorite(row.id)"
              :aria-label="`收藏 ${row.title}`"
            >
              <Icon name="favorites" :size="18" /></button
            ><RouterLink
              :to="`/opportunities/${row.id}`"
              class="icon-button"
              :aria-label="`查看 ${row.title}`"
              ><Icon name="arrow" :size="18"
            /></RouterLink>
          </div>
        </div>
      </article>
    </div>
    <Pagination :page="page" :count="count" @change="load" />
    <p class="data-note">
      演示样本不代表实时招录机会。正式报考请核对官方公告及截止日期。
    </p>
  </div>
</template>
