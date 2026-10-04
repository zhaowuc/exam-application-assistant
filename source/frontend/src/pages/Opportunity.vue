<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { get, post, act } from "../api";
import { zh, date, fieldLabels } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
import Modal from "../components/Modal.vue";
const route = useRoute(),
  row = ref(null),
  history = ref([]),
  matching = ref(null),
  loading = ref(true),
  error = ref(""),
  appModal = ref(false),
  candidate = ref(""),
  contact = ref(""),
  notes = ref(""),
  materials = ref(""),
  busy = ref(false);
async function load() {
  loading.value = true;
  try {
    const id = route.params.id;
    [row.value, history.value] = await Promise.all([
      get(`opportunities/${id}/`),
      get(`opportunities/${id}/history/`),
    ]);
    error.value = "";
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
onMounted(load);
async function match() {
  matching.value = await act(() =>
    get(`opportunities/${row.value.id}/matching/`),
  );
}
async function application() {
  busy.value = true;
  const result = await act(
    () =>
      post("applications/", {
        opportunity: row.value.id,
        candidate_name: candidate.value,
        contact: contact.value,
        notes: notes.value,
        materials: materials.value
          .split(/[、,，\n]/)
          .map((x) => x.trim())
          .filter(Boolean),
      }),
    "报考记录已保存，可在“我的报考”中查看",
  );
  if (result) appModal.value = false;
  busy.value = false;
}
async function plan() {
  await act(
    () =>
      post("application-plans/", {
        opportunity: row.value.id,
        title: row.value.title,
        exam_type: row.value.opportunity_type,
        target_name: row.value.organization,
        deadline: row.value.deadline,
      }),
    "已加入报考计划",
  );
}
</script>
<template>
  <div>
    <RouterLink
      :to="`/catalog/${row?.opportunity_type || 'civil'}`"
      class="back-link"
      ><Icon name="left" :size="17" /> 返回目标列表</RouterLink
    ><States :loading="loading" :error="error" @retry="load" /><template
      v-if="row"
      ><div class="detail-hero">
        <div>
          <div class="tag-row">
            <span>{{ zh(row.opportunity_type) }}</span
            ><span>{{ row.year }} 年 · {{ row.region }}</span
            ><span v-if="row.is_demo">本地演示</span>
          </div>
          <h1>{{ row.title }}</h1>
          <p>
            {{ row.organization }}
            <span v-if="row.department">/ {{ row.department }}</span>
          </p>
          <small>编号 {{ row.code }} · 截止 {{ date(row.deadline) }}</small>
        </div>
        <div class="detail-actions">
          <button
            class="button"
            @click="
              act(
                () => post('favorites/', { opportunity: row.id }),
                '已加入收藏',
              )
            "
          >
            <Icon name="favorites" :size="17" />收藏</button
          ><button class="button" @click="plan">加入计划</button
          ><button class="button primary" @click="appModal = true">
            记录报考 <Icon name="arrow" :size="17" />
          </button>
        </div>
      </div>
      <div class="detail-grid">
        <section class="card">
          <h2>资格与岗位条件</h2>
          <dl class="detail-list">
            <template
              v-for="key in [
                'slots',
                'education_required',
                'degree_required',
                'major_requirement',
                'political_status',
                'fresh_graduate_requirement',
                'household_requirement',
                'work_years',
                'grassroots_years',
                'max_age',
                'other_conditions',
              ]"
              :key="key"
              ><dt>{{ fieldLabels[key] }}</dt>
              <dd>{{ zh(row[key]) }}</dd></template
            >
          </dl>
          <h3>岗位说明</h3>
          <p class="prose">{{ row.description || "暂无补充说明" }}</p>
          <template
            v-if="
              row.graduate_detail || row.institution_detail || row.civil_detail
            "
            ><h3>专属信息</h3>
            <dl class="detail-list">
              <template
                v-for="(value, key) in row.graduate_detail ||
                row.institution_detail ||
                row.civil_detail"
                :key="key"
                ><template
                  v-if="
                    !['id', 'opportunity'].includes(key) &&
                    value !== '' &&
                    value !== null
                  "
                  ><dt>{{ fieldLabels[key] || key }}</dt>
                  <dd>
                    {{ Array.isArray(value) ? value.join("、") : value }}
                  </dd></template
                ></template
              >
            </dl></template
          >
        </section>
        <section class="card matching-card">
          <span class="eyebrow">QUALIFICATION CHECK</span>
          <h2>你与这个目标，<br />有多契合？</h2>
          <p class="muted">依据个人档案逐项检查。缺失和模糊条件会明确标记。</p>
          <button class="button primary" @click="match">
            <Icon name="layers" :size="17" />开始资格匹配</button
          ><RouterLink to="/profile" class="text-link"
            >先完善个人档案 <Icon name="arrow" :size="15"
          /></RouterLink>
          <div v-if="matching" class="matching-result">
            <span class="pill" :class="matching.status">{{
              matching.label
            }}</span>
            <div
              v-for="(check, i) in matching.checks"
              :key="i"
              class="check-row"
            >
              <Icon
                :name="check.status === 'eligible' ? 'success' : 'alert'"
                :size="18"
              />
              <div>
                <strong>{{ check.label }} · {{ zh(check.status) }}</strong
                ><small>{{ check.reason }}</small>
              </div>
            </div>
            <p class="data-note">{{ matching.summary }}</p>
          </div>
        </section>
      </div>
      <section class="card section">
        <div class="section-heading">
          <h2>历年数据</h2>
          <span class="muted">不是录取概率预测</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>年份</th>
                <th>名额</th>
                <th>报名人数</th>
                <th>审核人数</th>
                <th>录取人数</th>
                <th>最低分</th>
                <th>平均分</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in history" :key="item.id">
                <td>{{ item.year }}</td>
                <td>{{ item.slots }}</td>
                <td>{{ item.applicants }}</td>
                <td>{{ item.approved }}</td>
                <td>{{ item.admitted }}</td>
                <td>{{ item.minimum_score || "—" }}</td>
                <td>{{ item.average_score || "—" }}</td>
              </tr>
              <tr v-if="!history.length">
                <td colspan="7">暂无历史记录</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="data-note">
          数据来源：{{ row.source
          }}<a
            v-if="row.source_url"
            :href="row.source_url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-link"
          >
            官方来源（联网）<Icon name="external" :size="14"
          /></a>
        </p></section></template
    ><Modal v-if="appModal" title="记录报考信息" @close="appModal = false"
      ><p class="callout">仅保存本地报考记录，不向官方系统提交材料或报名。</p>
      <form class="form-stack" @submit.prevent="application">
        <label
          >报考姓名<input v-model="candidate" required maxlength="80" /></label
        ><label>联系方式<input v-model="contact" maxlength="80" /></label
        ><label
          >材料清单（每项换行或逗号分隔）<textarea
            v-model="materials"
            rows="3"
            placeholder="学历证明、资格证书…"
          /></label
        ><label>备注<textarea v-model="notes" rows="3" /></label
        ><button class="button primary" :disabled="busy">
          {{ busy ? "正在保存…" : "保存报考记录" }}
        </button>
      </form></Modal
    >
  </div>
</template>
