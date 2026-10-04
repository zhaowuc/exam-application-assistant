<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { get, post, act, query } from "../api";
import { zh } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
import Pagination from "../components/Pagination.vue";
import Modal from "../components/Modal.vue";
const router = useRouter(),
  tab = ref("papers"),
  papers = ref([]),
  questions = ref([]),
  type = ref("civil"),
  page = ref(1),
  count = ref(0),
  loading = ref(true),
  error = ref(""),
  selected = ref(null),
  answer = ref([]),
  result = ref(null),
  generateModal = ref(false),
  amount = ref(10),
  duration = ref(20),
  busy = ref(false),
  attempts = ref([]);
async function load(p = 1) {
  page.value = p;
  loading.value = true;
  error.value = "";
  try {
    const [a, b, c] = await Promise.all([
      get(`papers/?${query({ exam_type: type.value, page_size: 100 })}`),
      get(`questions/?${query({ exam_type: type.value, page: p })}`),
      get("attempts/?page_size=100"),
    ]);
    papers.value = a.results;
    questions.value = b.results;
    count.value = b.count;
    attempts.value = c.results.filter((a) => a.status === "in_progress");
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
async function start(paper) {
  busy.value = true;
  const data = await act(() => post("exams/start/", { paper: paper.id }));
  busy.value = false;
  if (data) router.push(`/exam/${data.id}`);
}
async function generate() {
  busy.value = true;
  const data = await act(
    () =>
      post("papers/generate/", {
        exam_type: type.value,
        count: Number(amount.value),
        duration_minutes: Number(duration.value),
      }),
    "组卷已完成",
  );
  if (data) {
    generateModal.value = false;
    await load();
  }
  busy.value = false;
}
function open(q) {
  selected.value = q;
  answer.value = [];
  result.value = null;
}
function choose(key) {
  if (result.value) return;
  if (selected.value.question_type === "multiple") {
    answer.value = answer.value.includes(key)
      ? answer.value.filter((v) => v !== key)
      : [...answer.value, key];
  } else answer.value = [key];
}
async function practice() {
  if (!answer.value.length) return;
  busy.value = true;
  result.value = await act(() =>
    post(`questions/${selected.value.id}/practice/`, { answer: answer.value }),
  );
  busy.value = false;
}
onMounted(() => load());
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">ONE QUESTION AT A TIME</div>
        <h1>在线刷题</h1>
        <p>单题巩固，专项组卷，限时模拟。把练习变成看得见的积累。</p>
      </div>
      <button class="button primary" @click="generateModal = true">
        <Icon name="plus" :size="18" />生成练习卷
      </button>
    </div>
    <div v-if="attempts.length" class="callout resume-list">
      <span>你有未完成的考试，答案已保存：</span
      ><RouterLink
        v-for="a in attempts"
        :key="a.id"
        :to="`/exam/${a.id}`"
        class="text-link"
        >继续考试 #{{ a.id }} <Icon name="arrow" :size="15"
      /></RouterLink>
    </div>
    <div class="practice-toolbar">
      <div class="tabs">
        <button :class="{ active: tab === 'papers' }" @click="tab = 'papers'">
          模拟试卷</button
        ><button
          :class="{ active: tab === 'questions' }"
          @click="tab = 'questions'"
        >
          单题练习
        </button>
      </div>
      <select v-model="type" aria-label="练习考试类型" @change="load()">
        <option
          v-for="t in ['civil', 'institution', 'graduate']"
          :key="t"
          :value="t"
        >
          {{ zh(t) }}
        </option>
      </select>
    </div>
    <States :loading="loading" :error="error" @retry="load(page)" /><template
      v-if="!loading && !error"
      ><div v-if="tab === 'papers'" class="record-grid">
        <article
          v-for="paper in papers"
          :key="paper.id"
          class="card paper-card"
        >
          <span class="paper-icon"><Icon name="file" :size="29" /></span>
          <div class="tag-row">
            <span>{{ zh(paper.exam_type) }}</span
            ><span>{{ paper.is_generated ? "自主组卷" : "精选试卷" }}</span>
          </div>
          <h2>{{ paper.title }}</h2>
          <p>{{ paper.subject || "综合练习" }}</p>
          <div class="paper-meta">
            <span>{{ paper.total_questions }} 道题</span
            ><span>{{ paper.total_score }} 分</span
            ><span>{{ paper.duration_minutes }} 分钟</span>
          </div>
          <button class="button primary" :disabled="busy" @click="start(paper)">
            开始考试 <Icon name="play" :size="16" />
          </button>
        </article>
        <States :empty="!papers.length" text="暂无可用试卷，试试自主组卷" />
      </div>
      <div v-else>
        <div class="question-list">
          <button
            v-for="q in questions"
            :key="q.id"
            class="card question-preview"
            @click="open(q)"
          >
            <span class="pill subtle"
              >{{ zh(q.question_type) }} · {{ q.subject }}</span
            >
            <h3>{{ q.stem }}</h3>
            <small>{{ q.knowledge_name }} · 难度 {{ q.difficulty }}</small
            ><Icon name="arrow" :size="18" />
          </button>
        </div>
        <Pagination
          :page="page"
          :count="count"
          @change="load"
        /></div></template
    ><Modal
      v-if="generateModal"
      title="生成专项练习卷"
      @close="generateModal = false"
      ><form class="form-stack" @submit.prevent="generate">
        <p class="muted">从本地题库随机抽题；完成考试后计入学习报告。</p>
        <label
          >考试方向<select v-model="type">
            <option
              v-for="t in ['civil', 'institution', 'graduate']"
              :key="t"
              :value="t"
            >
              {{ zh(t) }}
            </option>
          </select></label
        ><label
          >题目数量<input
            v-model="amount"
            type="number"
            min="1"
            max="100"
            required /></label
        ><label
          >考试时长（分钟）<input
            v-model="duration"
            type="number"
            min="1"
            max="600"
            required /></label
        ><button class="button primary" :disabled="busy">生成试卷</button>
      </form></Modal
    ><Modal v-if="selected" title="单题练习" wide @close="selected = null"
      ><span class="pill subtle"
        >{{ zh(selected.question_type) }} · {{ selected.subject }}</span
      >
      <h3 class="question-stem">{{ selected.stem }}</h3>
      <div class="answer-options">
        <button
          v-for="option in selected.options"
          :key="option.key"
          class="answer-option"
          :class="{
            selected: answer.includes(option.key),
            correct: result?.correct_answer?.includes(option.key),
          }"
          @click="choose(option.key)"
          :disabled="!!result"
        >
          <span>{{ option.key }}</span
          >{{ option.text
          }}<Icon v-if="answer.includes(option.key)" name="check" :size="18" />
        </button>
      </div>
      <button
        v-if="!result"
        class="button primary"
        @click="practice"
        :disabled="!answer.length || busy"
      >
        确认答案
      </button>
      <div
        v-else
        class="practice-result"
        :class="{ incorrect: !result.is_correct }"
      >
        <h3>
          {{ result.is_correct ? "回答正确" : "再想一想" }} · 标准答案
          {{ result.correct_answer.join("、") }}
        </h3>
        <p class="prose">{{ result.explanation }}</p>
      </div>
      <p class="data-note">
        单题用于即时练习；考试交卷后才统计成绩、错题和薄弱项。
      </p></Modal
    >
  </div>
</template>
