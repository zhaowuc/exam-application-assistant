<script setup>
import { ref, onMounted, computed } from "vue";
import { get, post, patch, act } from "../api";
import { date } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
import Modal from "../components/Modal.vue";
const scores = ref([]),
  wrong = ref([]),
  weak = ref([]),
  loading = ref(true),
  error = ref(""),
  tab = ref("scores"),
  selected = ref(null);
const average = computed(() =>
  scores.value.length
    ? (
        scores.value.reduce(
          (a, b) =>
            a + (Number(b.score) / Math.max(1, Number(b.total_score))) * 100,
          0,
        ) / scores.value.length
      ).toFixed(1)
    : "—",
);
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [a, b, c] = await Promise.all([
      get("scores/"),
      get("wrong-questions/?page_size=100"),
      get("weakness/"),
    ]);
    scores.value = a;
    wrong.value = b.results;
    weak.value = c;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
async function master(row) {
  const data = await act(
    () => patch(`wrong-questions/${row.id}/`, { mastered: !row.mastered }),
    "掌握状态已更新",
  );
  if (data) row.mastered = data.mastered;
}
onMounted(load);
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">PROGRESS, MADE VISIBLE</div>
        <h1>学习报告</h1>
        <p>回看你的练习，用错题与薄弱知识点安排下一步。</p>
      </div>
      <button
        class="button"
        @click="act(() => post('weakness/', {}), '分析已更新').then(load)"
      >
        <Icon name="refresh" :size="17" />重新分析
      </button>
    </div>
    <div class="stats-grid">
      <div class="stat-card">
        <div>
          <p>已完成考试</p>
          <strong>{{ scores.length }}</strong
          ><span>次认真练习</span>
        </div>
      </div>
      <div class="stat-card">
        <div>
          <p>平均得分率</p>
          <strong>{{ average }}<small>%</small></strong
          ><span>以不同试卷满分归一化</span>
        </div>
      </div>
      <div class="stat-card">
        <div>
          <p>待复习错题</p>
          <strong>{{ wrong.filter((x) => !x.mastered).length }}</strong
          ><span>让薄弱项成为突破口</span>
        </div>
      </div>
    </div>
    <div class="tabs">
      <button
        v-for="[key, title] in [
          ['scores', '成绩记录'],
          ['wrong', '错题本'],
          ['weak', '薄弱分析'],
        ]"
        :key="key"
        :class="{ active: tab === key }"
        @click="tab = key"
      >
        {{ title }}
      </button>
    </div>
    <States :loading="loading" :error="error" @retry="load" /><template
      v-if="!loading && !error"
      ><section v-if="tab === 'scores'" class="card">
        <h2>最近练习趋势</h2>
        <div
          v-if="scores.length"
          class="trend-chart"
          aria-label="最近十次考试得分率柱状图"
        >
          <div v-for="row in scores.slice(0, 10).reverse()" :key="row.id">
            <span
              >{{
                (
                  (Number(row.score) / Math.max(1, Number(row.total_score))) *
                  100
                ).toFixed(0)
              }}%</span
            ><i
              :style="{
                height:
                  Math.max(
                    3,
                    (Number(row.score) / Math.max(1, Number(row.total_score))) *
                      130,
                  ) + 'px',
              }"
            /><small>{{ date(row.submitted_at) }}</small>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>试卷</th>
                <th>得分</th>
                <th>正确 / 错误 / 未答</th>
                <th>完成日期</th>
                <th>报告</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in scores" :key="row.id">
                <td>{{ row.paper_title }}</td>
                <td>{{ row.score }} / {{ row.total_score }}</td>
                <td>
                  {{ row.correct_count }} / {{ row.incorrect_count }} /
                  {{ row.unanswered_count }}
                </td>
                <td>{{ date(row.submitted_at) }}</td>
                <td>
                  <RouterLink :to="`/exam/${row.id}`" class="text-link"
                    >查看 <Icon name="arrow" :size="15"
                  /></RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <States
          :empty="!scores.length"
          text="完成一次模拟考试，查看你的第一份报告"
        />
      </section>
      <div v-else-if="tab === 'wrong'" class="question-list">
        <article v-for="row in wrong" :key="row.id" class="card wrong-card">
          <div class="between">
            <span class="pill" :class="row.mastered ? 'approved' : 'rejected'"
              >{{ row.mastered ? "已掌握" : "待复习" }} · 错误
              {{ row.wrong_count }} 次</span
            ><button class="button small" @click="master(row)">
              {{ row.mastered ? "重新复习" : "标记掌握" }}
            </button>
          </div>
          <h3>{{ row.question_detail.stem }}</h3>
          <button class="text-link" @click="selected = row.question_detail">
            查看答案解析 <Icon name="right" :size="15" />
          </button>
        </article>
        <States :empty="!wrong.length" text="暂无错题，继续积累练习" />
      </div>
      <div v-else class="record-grid">
        <article v-for="row in weak" :key="row.id" class="card weakness-card">
          <div class="between">
            <span class="pill subtle">{{ row.subject }}</span
            ><span class="pill">{{ row.level }}</span>
          </div>
          <h2>{{ row.knowledge_name }}</h2>
          <div class="weakness-percentage">
            {{ row.accuracy }}<small>% 正确率</small>
          </div>
          <div class="progress-track">
            <span :style="{ width: row.accuracy + '%' }" />
          </div>
          <p class="muted">
            练习 {{ row.completed_count }} 题 · 正确 {{ row.correct_count }} 题
          </p>
          <p>{{ row.advice }}</p>
        </article>
        <States
          :empty="!weak.length"
          text="暂无分析数据，完成考试后会自动生成"
        /></div></template
    ><Modal v-if="selected" title="错题解析" wide @close="selected = null"
      ><h3 class="question-stem">{{ selected.stem }}</h3>
      <p v-for="o in selected.options" :key="o.key">
        {{ o.key }}. {{ o.text }}
      </p>
      <div class="reply-box">
        <strong>标准答案：{{ selected.correct_answer.join("、") }}</strong>
        <p class="prose">{{ selected.explanation }}</p>
      </div></Modal
    >
  </div>
</template>
