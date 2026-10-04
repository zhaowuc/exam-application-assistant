<script setup>
import { ref, onMounted } from "vue";
import { get, post, remove, act } from "../api";
import { zh } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
import Modal from "../components/Modal.vue";
const rows = ref([]),
  selected = ref([]),
  comparison = ref(null),
  loading = ref(true),
  error = ref(""),
  saved = ref([]);
async function load() {
  loading.value = true;
  try {
    const [a, b] = await Promise.all([
      get("favorites/?page_size=100"),
      get("comparisons/?page_size=100"),
    ]);
    rows.value = a.results;
    saved.value = b.results;
    error.value = "";
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
async function compare() {
  if (selected.value.length < 2 || selected.value.length > 4) {
    await act(() => Promise.reject(new Error("请选择2–4个目标")));
    return;
  }
  comparison.value = await act(
    () =>
      post("comparisons/", {
        title: "我的目标比较",
        opportunities: selected.value,
      }),
    "比较结果已保存",
  );
}
async function unfavorite(row) {
  if (confirm("移除这个收藏？")) {
    await act(() => remove(`favorites/${row.id}/`), "已移除收藏");
    selected.value = selected.value.filter((id) => id !== row.opportunity);
    load();
  }
}
onMounted(load);
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">CHOOSE WITH CONFIDENCE</div>
        <h1>收藏与比较</h1>
        <p>将感兴趣的目标放在一起，比较条件与历史情况。</p>
      </div>
      <button
        class="button primary"
        :disabled="selected.length < 2 || selected.length > 4"
        @click="compare"
      >
        比较所选（{{ selected.length }}/4）<Icon name="layers" :size="17" />
      </button>
    </div>
    <States
      :loading="loading"
      :error="error"
      :empty="!rows.length"
      text="收藏你的第一个报考目标"
      @retry="load"
    />
    <div v-if="!loading && !error" class="record-grid">
      <article v-for="row in rows" :key="row.id" class="card favorite-card">
        <div class="between">
          <label class="checkbox-label"
            ><input
              type="checkbox"
              :value="row.opportunity"
              v-model="selected"
            />加入比较</label
          ><button
            class="icon-button"
            @click="unfavorite(row)"
            aria-label="移除收藏"
          >
            <Icon name="trash" :size="17" />
          </button>
        </div>
        <RouterLink :to="`/opportunities/${row.opportunity}`"
          ><h2>{{ row.opportunity_detail.title }}</h2></RouterLink
        >
        <p class="muted">{{ row.opportunity_detail.organization }}</p>
        <div class="tag-row">
          <span>{{ zh(row.opportunity_detail.opportunity_type) }}</span
          ><span>{{ row.opportunity_detail.region }}</span
          ><span>{{ row.opportunity_detail.slots }} 名额</span>
        </div>
      </article>
    </div>
    <section v-if="saved.length" class="card section">
      <h2>已保存的比较</h2>
      <button
        v-for="row in saved"
        :key="row.id"
        class="saved-comparison"
        @click="comparison = row"
      >
        <span
          >{{ row.title }} ·
          {{ row.snapshot?.opportunities?.length || 0 }} 个目标</span
        ><Icon name="arrow" :size="17" />
      </button>
    </section>
    <Modal v-if="comparison" title="目标比较" wide @close="comparison = null"
      ><div class="table-wrap">
        <table class="comparison-table">
          <tbody>
            <tr>
              <th>目标</th>
              <td
                v-for="row in comparison.snapshot.opportunities"
                :key="row.id"
              >
                <strong>{{ row.title }}</strong>
              </td>
            </tr>
            <tr
              v-for="[key, label] in [
                ['organization', '单位'],
                ['region', '地区'],
                ['education_required', '学历'],
                ['major_requirement', '专业'],
                ['slots', '名额'],
                ['approved_count', '历史审核人数'],
                ['competition_ratio', '竞争比'],
                ['lowest_score', '最低分'],
                ['deadline', '截止时间'],
              ]"
              :key="key"
            >
              <th>{{ label }}</th>
              <td
                v-for="row in comparison.snapshot.opportunities"
                :key="row.id"
              >
                {{ row[key] ?? "—" }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="data-note">
        比较为创建时的数据快照。历史数据不代表当前录取机会。
      </p></Modal
    >
  </div>
</template>
