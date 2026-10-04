<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { get, post, patch, remove, api, act, toast, query } from "../api";
import { zh, fieldLabels, date } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
import Pagination from "../components/Pagination.vue";
import Modal from "../components/Modal.vue";
import ResourceForm from "../components/ResourceForm.vue";
const route = useRoute(),
  name = route.params.resource,
  rows = ref([]),
  schema = ref(null),
  loading = ref(true),
  error = ref(""),
  page = ref(1),
  count = ref(0),
  search = ref(""),
  status = ref(""),
  type = ref(""),
  year = ref(""),
  modal = ref(false),
  edit = ref(null),
  detail = ref(null),
  busy = ref(false),
  file = ref(null),
  importResult = ref(null);
const base = `admin/${name}/`;
async function load(p = 1) {
  page.value = p;
  loading.value = true;
  error.value = "";
  try {
    const [a, b] = await Promise.all([
      get(
        `${base}?${query({ page: p, search: search.value, status: status.value, exam_type: type.value, year: year.value })}`,
      ),
      get(base + "schema/"),
    ]);
    rows.value = a.results;
    count.value = a.count;
    schema.value = b;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
function heading(row) {
  return (
    row.title ||
    row.candidate_name ||
    row.name ||
    row.subject ||
    row.stem ||
    row.username ||
    row.key ||
    row.file_name ||
    row.action ||
    `记录 #${row.id}`
  );
}
function open(row = null) {
  edit.value = row;
  modal.value = true;
}
async function save(values) {
  busy.value = true;
  const result = await act(
    () =>
      edit.value
        ? patch(`${base}${edit.value.id}/`, values)
        : post(base, values),
    "记录已保存",
  );
  if (result) {
    modal.value = false;
    load(page.value);
  }
  busy.value = false;
}
async function destroy(row) {
  if (confirm(`确认删除“${heading(row)}”？关联数据可能受到影响。`)) {
    await act(() => remove(`${base}${row.id}/`), "已删除记录");
    load(page.value);
  }
}
async function download(template = false) {
  await act(() =>
    api(
      `${base}${template ? "template" : "export"}/?${query({ search: search.value, status: status.value, exam_type: type.value, year: year.value })}`,
      {
        download: true,
        filename: `${name}_${template ? "template" : "export"}.xlsx`,
      },
    ),
  );
}
async function upload(event) {
  const f = event.target.files[0];
  if (!f) return;
  busy.value = true;
  const body = new FormData();
  body.append("file", f);
  importResult.value = await act(() =>
    api(base + "import/", { method: "POST", body }),
  );
  if (importResult.value) {
    toast(
      `导入完成：成功 ${importResult.value.success_count}，失败 ${importResult.value.failure_count}`,
    );
    load(page.value);
  }
  event.target.value = "";
  busy.value = false;
}
onMounted(() => load());
</script>
<template>
  <div>
    <RouterLink to="/admin" class="back-link"
      ><Icon name="left" :size="17" /> 管理总览</RouterLink
    >
    <div class="page-heading">
      <div>
        <div class="eyebrow">STRUCTURED LOCAL DATA</div>
        <h1>{{ schema?.label || "数据管理" }}</h1>
        <p>共 {{ count }} 条记录 · 所有修改保存到本机，并记录审计日志。</p>
      </div>
      <div class="heading-actions">
        <button class="button" @click="download()">
          <Icon name="download" :size="17" />导出</button
        ><button
          v-if="
            schema &&
            !schema.readonly &&
            !['applications', 'service-requests'].includes(name)
          "
          class="button primary"
          @click="open()"
        >
          <Icon name="plus" :size="17" />新增
        </button>
      </div>
    </div>
    <div v-if="name === 'applications'" class="callout">
      此处管理本地报考记录：审核状态、审核说明、材料清单、成绩与结果；不向官方报名系统发送信息。
    </div>
    <form class="filter-bar" @submit.prevent="load()">
      <div class="search-input">
        <Icon name="search" :size="18" /><input
          v-model="search"
          aria-label="搜索管理记录"
          placeholder="搜索名称、正文或关键词"
        />
      </div>
      <select
        v-if="schema?.fields.some((f) => f.key === 'status')"
        v-model="status"
        aria-label="状态筛选"
        @change="load()"
      >
        <option value="">全部状态</option>
        <option
          v-for="option in schema.fields.find((f) => f.key === 'status')
            .choices"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </option></select
      ><template v-if="name === 'applications'"
        ><select v-model="type" aria-label="报考考试类型" @change="load()">
          <option value="">全部类型</option>
          <option
            v-for="t in ['civil', 'institution', 'graduate']"
            :key="t"
            :value="t"
          >
            {{ zh(t) }}
          </option></select
        ><input
          v-model="year"
          class="small-input"
          type="number"
          aria-label="报考年份"
          placeholder="年份" /></template
      ><button class="button">查询</button>
    </form>
    <States
      :loading="loading"
      :error="error"
      :empty="!rows.length"
      @retry="load(page)"
    />
    <section v-if="!loading && !error" class="card data-table-card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>
                {{ name === "applications" ? "报考人 / 目标" : "记录内容" }}
              </th>
              <th>分类 / 状态</th>
              <th>
                {{ name === "applications" ? "审核 / 成绩 / 结果" : "摘要" }}
              </th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.id">
              <td class="muted">#{{ row.id }}</td>
              <td>
                <strong class="table-title">{{ heading(row) }}</strong
                ><small class="table-sub">{{
                  row.opportunity_title ||
                  row.organization ||
                  row.subject ||
                  row.username ||
                  row.code ||
                  ""
                }}</small>
              </td>
              <td>
                <span class="pill subtle">{{
                  zh(
                    row.status ||
                      row.exam_type ||
                      row.opportunity_type ||
                      row.category ||
                      row.role ||
                      row.level,
                  )
                }}</span>
              </td>
              <td class="table-summary">
                {{
                  name === "applications"
                    ? `${row.review_notes || "待填写审核说明"} / ${row.score ?? "—"} / ${row.result || "—"}`
                    : row.summary ||
                      row.content ||
                      row.description ||
                      row.explanation ||
                      row.response ||
                      ""
                }}
              </td>
              <td>
                {{
                  date(
                    row.updated_at ||
                      row.created_at ||
                      row.date_joined ||
                      row.started_at,
                  )
                }}
              </td>
              <td>
                <div class="table-actions">
                  <button
                    class="icon-button"
                    @click="detail = row"
                    aria-label="查看记录详情"
                  >
                    <Icon name="file" :size="17" /></button
                  ><button
                    v-if="!schema.readonly"
                    class="icon-button"
                    @click="open(row)"
                    :aria-label="
                      name === 'applications' ? '审核报考记录' : '编辑记录'
                    "
                  >
                    <Icon name="edit" :size="17" /></button
                  ><button
                    v-if="!schema.readonly"
                    class="icon-button"
                    @click="destroy(row)"
                    aria-label="删除记录"
                  >
                    <Icon name="trash" :size="17" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <Pagination :page="page" :count="count" @change="load" />
    <section
      v-if="
        schema &&
        !schema.readonly &&
        !['users', 'applications', 'service-requests'].includes(name)
      "
      class="card section import-box"
    >
      <div>
        <h2>批量数据导入</h2>
        <p class="muted">
          请使用本版本模板，JSON列填写有效JSON。xlsx最多10000行、10MB；按行校验，错误可下载前查看。
        </p>
      </div>
      <div class="heading-actions">
        <button class="button" @click="download(true)">
          <Icon name="download" :size="17" />下载模板</button
        ><button class="button" :disabled="busy" @click="file.click()">
          <Icon name="upload" :size="17" />导入 XLSX</button
        ><input ref="file" type="file" accept=".xlsx" hidden @change="upload" />
      </div>
    </section>
    <Modal
      v-if="modal"
      :title="`${edit ? '编辑' : '新增'} · ${schema.label}`"
      wide
      @close="modal = false"
      ><p v-if="name === 'applications'" class="callout">
        修改审核状态时请填写审核说明；保存后会向报考人生成本地通知。
      </p>
      <p v-if="name === 'opportunities'" class="callout">
        专属详情 JSON：公务员需 recruiting_agency、employing_unit；事业单位需
        institution_name；研究生需
        university_name、university_code、college_name、program_name、program_code。编辑已有记录时可留空。
      </p>
      <ResourceForm
        :fields="schema.fields"
        :initial="edit"
        :busy="busy"
        @save="save" /></Modal
    ><Modal v-if="detail" title="记录详情" wide @close="detail = null"
      ><dl class="detail-list">
        <template v-for="(value, key) in detail" :key="key"
          ><dt>{{ fieldLabels[key] || key }}</dt>
          <dd class="prose">
            {{
              typeof value === "object"
                ? JSON.stringify(value, null, 2)
                : (value ?? "—")
            }}
          </dd></template
        >
      </dl></Modal
    ><Modal
      v-if="importResult"
      title="导入结果"
      wide
      @close="importResult = null"
      ><p>
        总计 {{ importResult.total_rows }} 行；成功
        {{ importResult.success_count }}；失败
        {{ importResult.failure_count }}；更新
        {{ importResult.duplicate_count }}。
      </p>
      <div
        v-for="row in importResult.error_report"
        :key="row.row"
        class="form-error"
      >
        第 {{ row.row }} 行：{{ row.error }}
      </div>
      <p v-if="!importResult.error_report.length" class="callout">
        所有非空数据行均通过校验并保存。
      </p></Modal
    >
  </div>
</template>
