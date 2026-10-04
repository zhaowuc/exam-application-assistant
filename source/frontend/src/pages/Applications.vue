<script setup>
import { ref, onMounted } from "vue";
import { get, post, patch, remove, act } from "../api";
import { zh, date } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
import Modal from "../components/Modal.vue";
const records = ref([]),
  plans = ref([]),
  loading = ref(true),
  error = ref(""),
  tab = ref("records"),
  modal = ref(false),
  edit = ref(null),
  busy = ref(false),
  form = ref({}),
  recordEdit = ref(null),
  recordForm = ref({});
function editRecord(row) {
  recordEdit.value = row;
  recordForm.value = {
    candidate_name: row.candidate_name,
    contact: row.contact,
    notes: row.notes,
    materials: row.materials.join("、"),
  };
}
async function saveRecord() {
  busy.value = true;
  const result = await act(
    () =>
      patch(`applications/${recordEdit.value.id}/`, {
        ...recordForm.value,
        status: "submitted",
        materials: recordForm.value.materials
          .split(/[、,，\n]/)
          .map((s) => s.trim())
          .filter(Boolean),
      }),
    "报考记录已更新并重新提交",
  );
  if (result) {
    recordEdit.value = null;
    load();
  }
  busy.value = false;
}
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [a, b] = await Promise.all([
      get("applications/?page_size=100"),
      get("application-plans/?page_size=100"),
    ]);
    records.value = a.results;
    plans.value = b.results;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
function open(obj = null) {
  edit.value = obj;
  form.value = obj
    ? {
        title: obj.title,
        target_name: obj.target_name,
        exam_type: obj.exam_type,
        status: obj.status,
        registration_start: obj.registration_start || "",
        registration_end: obj.registration_end || "",
        exam_date: obj.exam_date || "",
        notes: obj.notes,
        remind: obj.remind,
      }
    : {
        title: "",
        target_name: "",
        exam_type: "civil",
        status: "preparing",
        registration_start: "",
        registration_end: "",
        exam_date: "",
        notes: "",
        remind: true,
      };
  modal.value = true;
}
async function save() {
  busy.value = true;
  const data = { ...form.value };
  for (const key of ["registration_start", "registration_end", "exam_date"])
    data[key] = data[key] || null;
  const result = await act(
    () =>
      edit.value
        ? patch(`application-plans/${edit.value.id}/`, data)
        : post("application-plans/", data),
    "计划已保存",
  );
  if (result) {
    modal.value = false;
    load();
  }
  busy.value = false;
}
async function cancel(obj) {
  if (!confirm("确认取消这条本地报考记录？不会影响官方报名。")) return;
  await act(
    () => patch(`applications/${obj.id}/`, { status: "cancelled" }),
    "记录已取消",
  );
  load();
}
async function deletePlan(obj) {
  if (confirm("确认删除这个计划？")) {
    await act(() => remove(`application-plans/${obj.id}/`), "计划已删除");
    load();
  }
}
onMounted(load);
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">KEEP YOUR NEXT STEP IN SIGHT</div>
        <h1>我的报考</h1>
        <p>记录本地报考进度，让材料、审核和时间安排井然有序。</p>
      </div>
      <button class="button primary" @click="open()">
        <Icon name="plus" :size="17" />新增计划
      </button>
    </div>
    <div class="tabs">
      <button :class="{ active: tab === 'records' }" @click="tab = 'records'">
        报考记录 <span>{{ records.length }}</span></button
      ><button :class="{ active: tab === 'plans' }" @click="tab = 'plans'">
        时间与计划 <span>{{ plans.length }}</span>
      </button>
    </div>
    <States :loading="loading" :error="error" @retry="load" /><template
      v-if="!loading && !error"
      ><div v-if="tab === 'records'">
        <p class="callout">
          本页记录仅用于本地管理，管理员审核也不代表官方资格审核。请在官方报名平台完成正式报名。
        </p>
        <div class="record-grid">
          <article
            v-for="row in records"
            :key="row.id"
            class="card application-card"
          >
            <div class="between">
              <span class="pill subtle"
                >{{ zh(row.exam_type) }} · {{ row.year }}</span
              ><span class="pill" :class="row.status">{{
                zh(row.status)
              }}</span>
            </div>
            <RouterLink :to="`/opportunities/${row.opportunity}`"
              ><h2>{{ row.opportunity_title }}</h2></RouterLink
            >
            <p class="muted">{{ row.organization }}</p>
            <dl class="mini-list">
              <dt>报考人</dt>
              <dd>{{ row.candidate_name }}</dd>
              <dt>材料清单</dt>
              <dd>{{ row.materials.join("、") || "未填写" }}</dd>
              <dt>成绩 / 结果</dt>
              <dd>
                {{ row.score ?? "未录入" }} / {{ row.result || "未公布" }}
              </dd>
            </dl>
            <div v-if="row.review_notes" class="reply-box">
              <strong>审核说明</strong>
              <p>{{ row.review_notes }}</p>
            </div>
            <div class="between record-footer">
              <button
                v-if="['draft', 'submitted', 'rejected'].includes(row.status)"
                class="button small"
                @click="editRecord(row)"
              >
                完善记录
              </button>
              <small class="muted">{{ date(row.updated_at) }} 更新</small
              ><button
                v-if="!['completed', 'cancelled'].includes(row.status)"
                class="button small"
                @click="cancel(row)"
              >
                取消记录
              </button>
            </div>
          </article>
        </div>
        <States :empty="!records.length" text="还没有报考记录"
          ><RouterLink to="/catalog/civil" class="button primary"
            >查找报考目标</RouterLink
          ></States
        >
      </div>
      <div v-else class="plan-list">
        <article v-for="row in plans" :key="row.id" class="card plan-card">
          <div class="plan-date">
            <Icon name="clock" :size="22" /><strong>{{
              row.exam_date ? date(row.exam_date) : "待安排"
            }}</strong
            ><span>考试日期</span>
          </div>
          <div class="plan-main">
            <span class="pill subtle"
              >{{ zh(row.status) }} · {{ zh(row.exam_type) }}</span
            >
            <h2>{{ row.title || row.target_name || "我的报考计划" }}</h2>
            <p>
              报名时间：{{ date(row.registration_start) }} —
              {{ date(row.registration_end) }}
            </p>
            <small class="muted">{{ row.notes || "暂无备注" }}</small>
          </div>
          <div class="plan-buttons">
            <button
              class="icon-button"
              @click="open(row)"
              aria-label="编辑计划"
            >
              <Icon name="edit" :size="18" /></button
            ><button
              class="icon-button"
              @click="deletePlan(row)"
              aria-label="删除计划"
            >
              <Icon name="trash" :size="18" />
            </button>
          </div>
        </article>
        <States
          :empty="!plans.length"
          text="为下一场考试制定一个计划"
        /></div></template
    ><Modal
      v-if="modal"
      :title="edit ? '编辑报考计划' : '新增报考计划'"
      @close="modal = false"
      ><form class="form-stack" @submit.prevent="save">
        <label
          >计划标题<input
            v-model="form.title"
            required
            maxlength="255" /></label
        ><label
          >目标单位<input v-model="form.target_name" maxlength="255"
        /></label>
        <div class="form-grid">
          <label
            >类型<select v-model="form.exam_type">
              <option
                v-for="t in ['civil', 'institution', 'graduate']"
                :key="t"
                :value="t"
              >
                {{ zh(t) }}
              </option>
            </select></label
          ><label
            >进度<select v-model="form.status">
              <option
                v-for="s in [
                  'preparing',
                  'planned',
                  'registered',
                  'paid',
                  'completed',
                  'cancelled',
                ]"
                :key="s"
                :value="s"
              >
                {{ zh(s) }}
              </option>
            </select></label
          ><label
            >报名开始<input
              v-model="form.registration_start"
              type="date" /></label
          ><label
            >报名截止<input
              v-model="form.registration_end"
              type="date"
              :min="form.registration_start" /></label
          ><label>考试日期<input v-model="form.exam_date" type="date" /></label>
        </div>
        <label>备注<textarea v-model="form.notes" rows="3" /></label
        ><label class="checkbox-label"
          ><input v-model="form.remind" type="checkbox" />开启计划提醒</label
        ><button class="button primary" :disabled="busy">保存计划</button>
      </form></Modal
    >
    <Modal v-if="recordEdit" title="完善报考记录" @close="recordEdit = null">
      <p class="callout">更新材料后会重新提交给本机管理员；不影响官方报名。</p>
      <form class="form-stack" @submit.prevent="saveRecord">
        <label
          >报考姓名<input
            v-model="recordForm.candidate_name"
            required
            maxlength="80"
        /></label>
        <label
          >联系方式<input v-model="recordForm.contact" maxlength="80"
        /></label>
        <label
          >材料清单（逗号分隔）<textarea
            v-model="recordForm.materials"
            rows="3"
          />
        </label>
        <label>备注<textarea v-model="recordForm.notes" rows="3" /></label>
        <button class="button primary" :disabled="busy">更新并重新提交</button>
      </form>
    </Modal>
  </div>
</template>
