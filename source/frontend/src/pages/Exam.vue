<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { useRoute, onBeforeRouteLeave, useRouter } from "vue-router";
import { get, post, act, toast } from "../api";
import { zh } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
const route = useRoute(),
  router = useRouter(),
  data = ref(null),
  index = ref(0),
  loading = ref(true),
  error = ref(""),
  busy = ref(false),
  saveStatus = ref("已从本地恢复"),
  remaining = ref(0),
  changed = ref(false),
  submitting = ref(false);
let clock,
  autosave,
  epoch = 0,
  revision = 0,
  savedRevision = 0,
  saveJob = null,
  timedQuestion = null,
  timedAt = Date.now();
const timeRemainders = {};
const question = computed(() => data.value?.questions[index.value]),
  record = computed(() =>
    data.value?.answers.find((a) => a.question === question.value?.id),
  ),
  completed = computed(
    () => data.value?.answers.filter((a) => a.answer.length).length || 0,
  ),
  time = computed(
    () =>
      `${String(Math.floor(remaining.value / 60)).padStart(2, "0")}:${String(remaining.value % 60).padStart(2, "0")}`,
  );
function accountTime() {
  const now = Date.now();
  if (data.value?.status === "in_progress" && timedQuestion !== null) {
    const previous = data.value.answers.find(
      (a) => a.question === timedQuestion,
    );
    const elapsed =
      Math.max(0, (now - timedAt) / 1000) +
      (timeRemainders[timedQuestion] || 0);
    const seconds = Math.floor(elapsed);
    timeRemainders[timedQuestion] = elapsed - seconds;
    if (previous && seconds) {
      previous.time_seconds += seconds;
      revision++;
      changed.value = true;
    }
  }
  timedQuestion = question.value?.id ?? null;
  timedAt = now;
}
watch(index, accountTime, { flush: "sync" });
function payload() {
  accountTime();
  return {
    answers: data.value.answers.map((a) => ({ ...a })),
    current_index: index.value,
  };
}
async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await get(`attempts/${route.params.id}/`);
    index.value = data.value.current_index;
    remaining.value = data.value.remaining_seconds;
    epoch = Date.now() + remaining.value * 1000;
    timedQuestion = question.value?.id ?? null;
    timedAt = Date.now();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
function choose(key) {
  if (data.value.status !== "in_progress" || busy.value) return;
  const answer = record.value.answer;
  if (question.value.question_type === "multiple")
    record.value.answer = answer.includes(key)
      ? answer.filter((x) => x !== key)
      : [...answer, key];
  else record.value.answer = [key];
  revision++;
  changed.value = true;
  saveStatus.value = "有未保存答案";
}
function mark() {
  record.value.is_marked = !record.value.is_marked;
  revision++;
  changed.value = true;
}
async function save(silent = false) {
  if (!data.value || data.value.status !== "in_progress") return true;
  if (saveJob) return saveJob;
  const snapshot = payload(),
    sentRevision = revision;
  saveStatus.value = "正在保存…";
  saveJob = (async () => {
    try {
      const result = await post(`attempts/${data.value.id}/save/`, snapshot);
      savedRevision = sentRevision;
      changed.value = revision !== savedRevision;
      saveStatus.value = changed.value ? "有未保存答案" : "答案已保存";
      if (result.status !== "in_progress") data.value = result;
      return true;
    } catch (e) {
      saveStatus.value = "保存失败，请重试";
      if (!silent) toast(e.message, "error");
      return false;
    } finally {
      saveJob = null;
    }
  })();
  return saveJob;
}
async function submit(auto = false) {
  if (submitting.value || data.value?.status !== "in_progress") return;
  if (!auto && !confirm("确认交卷？交卷后不能修改答案。")) return;
  submitting.value = true;
  busy.value = true;
  try {
    if (saveJob) await saveJob;
    const result = await post(`attempts/${data.value.id}/submit/`, payload());
    data.value = result;
    changed.value = false;
    toast(auto ? "时间已到，已按已保存答案交卷" : "交卷成功，学习报告已生成");
  } catch (e) {
    toast(e.message, "error");
  } finally {
    busy.value = false;
    submitting.value = false;
  }
}
function unload(e) {
  if (changed.value && data.value?.status === "in_progress") {
    e.preventDefault();
    e.returnValue = "";
  }
}
onMounted(async () => {
  await load();
  clock = setInterval(() => {
    if (data.value?.status === "in_progress") {
      remaining.value = Math.max(0, Math.ceil((epoch - Date.now()) / 1000));
      if (remaining.value === 0) submit(true);
    }
  }, 1000);
  autosave = setInterval(() => {
    accountTime();
    if (changed.value) save(true);
  }, 5000);
  window.addEventListener("beforeunload", unload);
});
onBeforeUnmount(() => {
  clearInterval(clock);
  clearInterval(autosave);
  window.removeEventListener("beforeunload", unload);
});
onBeforeRouteLeave(async () => {
  if (changed.value && data.value?.status === "in_progress") {
    if (!confirm("离开前保存答案？可稍后继续考试。")) return false;
    return await save();
  }
});
</script>
<template>
  <div>
    <States :loading="loading" :error="error" @retry="load" /><template
      v-if="data"
      ><div class="page-heading">
        <div>
          <div class="eyebrow">STAY FOCUSED</div>
          <h1>{{ data.paper_title }}</h1>
          <p>
            {{
              data.status === "in_progress"
                ? "沉下心，认真完成这一题。"
                : "每一次练习，都在让下一步更清晰。"
            }}
          </p>
        </div>
        <span
          v-if="data.status === 'in_progress'"
          class="exam-clock"
          :class="{ urgent: remaining < 60 }"
          ><Icon name="clock" :size="21" />{{ time }}</span
        ><span v-else class="pill approved">{{ zh(data.status) }}</span>
      </div>
      <template v-if="data.status === 'in_progress'"
        ><div class="exam-layout">
          <section class="card exam-question">
            <div class="between">
              <span class="pill subtle"
                >第 {{ index + 1 }} / {{ data.questions.length }} 题 ·
                {{ zh(question.question_type) }}</span
              ><span>{{ question.paper_points }} 分</span>
            </div>
            <h2 class="question-stem">{{ question.stem }}</h2>
            <div class="answer-options">
              <button
                v-for="option in question.options"
                :key="option.key"
                class="answer-option"
                :class="{ selected: record?.answer?.includes(option.key) }"
                @click="choose(option.key)"
              >
                <span>{{ option.key }}</span
                >{{ option.text
                }}<Icon
                  v-if="record?.answer?.includes(option.key)"
                  name="check"
                  :size="19"
                />
              </button>
            </div>
            <div class="exam-question-bottom">
              <button class="button small" @click="mark">
                {{ record?.is_marked ? "取消标记" : "标记此题" }}
              </button>
              <div>
                <button class="button" :disabled="index === 0" @click="index--">
                  <Icon name="left" :size="17" />上一题</button
                ><button
                  class="button primary"
                  :disabled="index === data.questions.length - 1"
                  @click="index++"
                >
                  下一题 <Icon name="right" :size="17" />
                </button>
              </div>
            </div>
          </section>
          <aside class="card answer-sheet">
            <h2>答题卡</h2>
            <p>{{ completed }} / {{ data.questions.length }} 题已作答</p>
            <div class="answer-grid">
              <button
                v-for="(q, i) in data.questions"
                :key="q.id"
                :class="{
                  current: index === i,
                  answered: data.answers.find((a) => a.question === q.id)
                    ?.answer?.length,
                  marked: data.answers.find((a) => a.question === q.id)
                    ?.is_marked,
                }"
                @click="index = i"
                :aria-label="`转到第 ${i + 1} 题`"
              >
                {{ i + 1 }}
              </button>
            </div>
            <div class="save-status">
              <span class="status-dot" />{{ saveStatus }}
            </div>
            <button class="button" :disabled="busy" @click="save()">
              <Icon name="done" :size="17" />保存答案</button
            ><button class="button primary" :disabled="busy" @click="submit()">
              {{ busy ? "正在交卷…" : "交卷并查看报告" }}
            </button>
            <p class="data-note">
              每 5 秒自动保存。倒计时以服务器截止时间为准。
            </p>
          </aside>
        </div></template
      ><template v-else
        ><section class="score-hero">
          <div>
            <span class="eyebrow">YOUR LEARNING SNAPSHOT</span>
            <h2>本次练习已完成</h2>
            <p>{{ data.report.summary }}</p>
          </div>
          <div class="score-value">
            <strong>{{ data.score }}</strong
            ><span>/ {{ data.total_score }} 分</span>
          </div>
        </section>
        <div class="stats-grid">
          <div class="stat-card">
            <div>
              <p>正确题数</p>
              <strong>{{ data.correct_count }}</strong>
            </div>
          </div>
          <div class="stat-card">
            <div>
              <p>错误 / 未答</p>
              <strong
                >{{ data.incorrect_count }} /
                {{ data.unanswered_count }}</strong
              >
            </div>
          </div>
          <div class="stat-card">
            <div>
              <p>正确率</p>
              <strong>{{ data.report.accuracy }}<small>%</small></strong>
            </div>
          </div>
        </div>
        <div class="report-questions">
          <details
            v-for="(row, i) in data.report.details"
            :key="row.question"
            class="card report-question"
          >
            <summary>
              <span
                class="pill"
                :class="row.is_correct ? 'approved' : 'rejected'"
                >{{ row.is_correct ? "正确" : "需复习" }}</span
              ><strong>{{ i + 1 }}. {{ row.stem }}</strong
              ><Icon name="right" :size="18" />
            </summary>
            <div class="report-answer">
              <p v-for="o in row.options" :key="o.key">
                {{ o.key }}. {{ o.text }}
              </p>
              <div class="reply-box">
                <p>
                  你的答案：{{ row.answer.join("、") || "未作答" }} ·
                  标准答案：{{ row.correct_answer.join("、") }}
                </p>
                <p class="prose">{{ row.explanation }}</p>
                <small>知识点：{{ row.knowledge_name }}</small>
              </div>
            </div>
          </details>
        </div>
        <RouterLink to="/scores" class="button primary"
          >查看学习报告 <Icon name="arrow" :size="17" /></RouterLink></template
    ></template>
  </div>
</template>
