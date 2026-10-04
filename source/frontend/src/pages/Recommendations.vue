<script setup>
import { ref, onMounted } from "vue";
import { get, post, act } from "../api";
import { zh } from "../labels";
import States from "../components/States.vue";
import Icon from "../components/Icon.vue";
import Modal from "../components/Modal.vue";
const rows = ref([]),
  loading = ref(true),
  error = ref(""),
  type = ref(""),
  selected = ref(null);
async function load(save = false) {
  loading.value = true;
  error.value = "";
  try {
    const path = `recommendations/${type.value ? "?opportunity_type=" + type.value : ""}`;
    const data = await (save ? post(path, {}) : get(path));
    rows.value = data.results;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
onMounted(() => load());
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">LESS GUESSWORK, MORE CLARITY</div>
        <h1>发现适合你的方向</h1>
        <p>基于档案与本地数据的可解释推荐，不是录取概率预测。</p>
      </div>
      <RouterLink to="/profile" class="button"
        >完善档案 <Icon name="arrow" :size="17"
      /></RouterLink>
    </div>
    <div class="callout">
      档案不完整时，推荐会提示待确认条件。资格不符合的目标不会进入列表；最终以官方审查为准。
    </div>
    <div class="filter-bar">
      <select v-model="type" aria-label="推荐考试类型" @change="load()">
        <option value="">全部方向</option>
        <option
          v-for="t in ['civil', 'institution', 'graduate']"
          :key="t"
          :value="t"
        >
          {{ zh(t) }}
        </option></select
      ><button class="button primary" @click="load(true)">
        <Icon name="refresh" :size="17" />重新计算并保存
      </button>
    </div>
    <States
      :loading="loading"
      :error="error"
      :empty="!rows.length"
      text="暂时没有符合条件的目标"
      @retry="load()"
    />
    <div v-if="!loading && !error" class="recommendation-list">
      <article
        v-for="(row, i) in rows"
        :key="row.opportunity.id"
        class="card recommendation-card"
      >
        <div class="recommendation-rank">
          {{ String(i + 1).padStart(2, "0") }}
        </div>
        <div class="recommendation-main">
          <div class="tag-row">
            <span>{{ zh(row.opportunity.opportunity_type) }}</span
            ><span>{{ zh(row.level) }}</span
            ><span>{{ zh(row.qualification_status) }}</span>
          </div>
          <RouterLink :to="`/opportunities/${row.opportunity.id}`"
            ><h2>{{ row.opportunity.title }}</h2></RouterLink
          >
          <p>
            {{ row.opportunity.organization }} · {{ row.opportunity.region }}
          </p>
          <small class="muted">{{
            row.risks.slice(0, 2).join("；") ||
            "主要资格条件符合，请继续核对官方公告。"
          }}</small>
        </div>
        <div class="recommendation-score">
          <strong>{{ row.score }}</strong
          ><span>匹配指数 / 100</span
          ><button class="text-link" @click="selected = row">
            查看依据 <Icon name="right" :size="15" />
          </button>
        </div>
      </article>
    </div>
    <Modal v-if="selected" title="推荐依据" @close="selected = null"
      ><h3>{{ selected.opportunity.title }}</h3>
      <p class="muted">{{ selected.explanation }}</p>
      <div
        v-for="(item, key) in selected.breakdown"
        :key="key"
        class="dimension"
      >
        <div>
          <span>{{
            {
              qualification: "资格",
              major: "专业",
              region: "地区",
              slots: "名额",
              competition: "竞争",
              score: "成绩",
              school: "院校",
            }[key]
          }}</span
          ><strong
            >{{ item.score }} <small>权重 {{ item.weight }}%</small></strong
          >
        </div>
        <div class="progress-track">
          <span :style="{ width: item.score + '%' }" />
        </div>
      </div>
      <h3>需要留意</h3>
      <ul>
        <li v-for="risk in selected.risks" :key="risk">{{ risk }}</li>
      </ul>
      <p>{{ selected.advice }}</p></Modal
    >
  </div>
</template>
