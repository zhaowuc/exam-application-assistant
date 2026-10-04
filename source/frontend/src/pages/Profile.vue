<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { get, patch, post, act, session, saveSession } from "../api";
import { zh, fieldLabels } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
const router = useRouter(),
  form = ref(null),
  loading = ref(true),
  error = ref(""),
  majors = ref([]),
  busy = ref(false),
  examProfiles = ref([]),
  texts = ref({}),
  passwords = ref({ old_password: "", new_password: "" });
const arrays = ["certificates", "target_regions", "school_preferences"];
const shortFields = [
  "nickname",
  "real_name",
  "region",
  "degree",
  "major_text",
  "graduation_status",
  "political_status",
  "household_region",
  "origin_region",
];
async function load() {
  loading.value = true;
  try {
    [form.value, majors.value] = await Promise.all([
      get("profile/"),
      get("majors/"),
    ]);
    examProfiles.value = (await get("exam-profiles/?page_size=100")).results;
    for (const key of arrays) texts.value[key] = form.value[key].join("、");
    texts.value.mock_scores = JSON.stringify(form.value.mock_scores, null, 2);
    error.value = "";
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
async function save() {
  busy.value = true;
  const data = { ...form.value };
  try {
    for (const key of arrays)
      data[key] = texts.value[key]
        .split(/[、,，\n]/)
        .map((v) => v.trim())
        .filter(Boolean);
    data.mock_scores = JSON.parse(texts.value.mock_scores || "{}");
    await patch("profile/", data);
    await patch("auth/me/", {
      phone: session.user.phone,
      email: session.user.email,
    });
    (await import("../api")).toast("个人档案已保存");
  } catch (e) {
    (await import("../api")).toast(e.message, "error");
  } finally {
    busy.value = false;
  }
}
async function changePassword() {
  busy.value = true;
  const data = await act(() => post("auth/change-password/", passwords.value));
  if (data) {
    saveSession({ access: "", refresh: "", user: null });
    router.push("/login");
  }
  busy.value = false;
}
async function toggle(type) {
  const obj = examProfiles.value.find((x) => x.exam_type === type);
  await act(
    () =>
      obj
        ? patch(`exam-profiles/${obj.id}/`, { enabled: !obj.enabled })
        : post("exam-profiles/", { exam_type: type, enabled: true }),
    "订阅偏好已更新",
  );
  examProfiles.value = (await get("exam-profiles/?page_size=100")).results;
}
onMounted(load);
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">A PROFILE THAT KNOWS YOUR GOALS</div>
        <h1>个人中心</h1>
        <p>完善档案，让资格匹配与推荐更有依据。</p>
      </div>
      <span class="pill"
        >{{ zh(session.user?.role) }} · {{ session.user?.username }}</span
      >
    </div>
    <States :loading="loading" :error="error" @retry="load" /><template
      v-if="form && !loading"
      ><form @submit.prevent="save" class="card profile-card">
        <div class="section-heading">
          <h2>个人与报考档案</h2>
          <button class="button primary" :disabled="busy">
            <Icon name="done" :size="17" />保存档案
          </button>
        </div>
        <div class="form-grid">
          <label v-for="key in shortFields" :key="key"
            >{{ fieldLabels[key]
            }}<input
              v-model="form[key]"
              :maxlength="key === 'major_text' ? 100 : 64" /></label
          ><label
            >出生年份<input
              v-model.number="form.birth_year"
              type="number"
              min="1900"
              :max="new Date().getFullYear()" /></label
          ><label
            >学历<select v-model="form.education">
              <option value="">未填写</option>
              <option
                v-for="[k, t] in [
                  ['high_school', '高中及以下'],
                  ['college', '大专'],
                  ['bachelor', '本科'],
                  ['master', '硕士'],
                  ['doctor', '博士'],
                ]"
                :key="k"
                :value="k"
              >
                {{ t }}
              </option>
            </select></label
          ><label
            >目录专业<select v-model="form.major">
              <option :value="null">未选择（使用手填专业）</option>
              <option v-for="major in majors" :key="major.id" :value="major.id">
                {{ major.name }}
              </option>
            </select></label
          ><label
            >应届毕业生<select v-model="form.is_fresh_graduate">
              <option :value="null">不确定 / 未填写</option>
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select></label
          ><label
            >工作年限<input
              v-model.number="form.work_years"
              type="number"
              min="0"
              max="80" /></label
          ><label
            >基层工作年限<input
              v-model.number="form.grassroots_years"
              type="number"
              min="0"
              max="80" /></label
          ><label
            >联系电话<input
              v-model="session.user.phone"
              maxlength="32"
              type="tel" /></label
          ><label
            >电子邮箱<input
              v-model="session.user.email"
              type="email"
              maxlength="254" /></label
          ><label v-for="key in arrays" :key="key"
            >{{ fieldLabels[key] }}（逗号分隔）<input v-model="texts[key]"
          /></label>
        </div>
        <label class="form-block"
          >工作经历<textarea v-model="form.work_experience" rows="3" /></label
        ><label class="form-block"
          >模拟成绩（JSON，例如 {"civil": 125}）<textarea
            v-model="texts.mock_scores"
            rows="3"
            class="code-input"
          />
        </label>
        <p class="data-note">
          年龄按当前年份估算；官方公告的年龄计算基准可能不同，请人工核对。
        </p>
      </form>
      <section class="card section">
        <h2>消息订阅方向</h2>
        <p class="muted">选择接收哪个考试方向的本地通知。</p>
        <div class="subscription-grid">
          <button
            v-for="type in ['civil', 'institution', 'graduate']"
            :key="type"
            class="subscription"
            :class="{
              selected: examProfiles.find((x) => x.exam_type === type)?.enabled,
            }"
            @click="toggle(type)"
          >
            <Icon :name="type" :size="22" /><span>{{ zh(type) }}</span
            ><Icon
              v-if="examProfiles.find((x) => x.exam_type === type)?.enabled"
              name="check"
              :size="18"
            /><span v-else>未订阅</span>
          </button>
        </div>
      </section>
      <form class="card section security-card" @submit.prevent="changePassword">
        <h2>账号安全</h2>
        <p class="muted">
          正式使用前请修改默认密码。修改后会退出所有登录会话。
        </p>
        <div class="form-grid">
          <label
            >原密码<input
              v-model="passwords.old_password"
              type="password"
              required
              autocomplete="current-password" /></label
          ><label
            >新密码<input
              v-model="passwords.new_password"
              type="password"
              required
              minlength="8"
              autocomplete="new-password"
          /></label>
        </div>
        <button class="button" :disabled="busy">修改密码并重新登录</button>
      </form></template
    >
  </div>
</template>
