<script setup>
import { ref, onMounted } from "vue";
import { get } from "../api";
import { zh } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
const data = ref(null),
  loading = ref(true),
  error = ref("");
async function load() {
  loading.value = true;
  try {
    data.value = await get("admin/dashboard/");
    error.value = "";
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">EVERYTHING, UNDER CONTROL</div>
        <h1>管理空间</h1>
        <p>统一管理招考信息、报考数据、公共服务与学习内容。</p>
      </div>
      <RouterLink to="/admin/operations" class="button"
        ><Icon name="settings" :size="17" />系统运行</RouterLink
      >
    </div>
    <States :loading="loading" :error="error" @retry="load" /><template
      v-if="data"
      ><section class="admin-banner">
        <div>
          <span class="eyebrow light">LOCAL-FIRST ADMINISTRATION</span>
          <h2>每一条信息，<br />都值得认真管理。</h2>
          <p>新增的公共服务与报考数据模块已接入本地数据库。</p>
        </div>
        <Icon name="admin" :size="90" />
      </section>
      <div class="admin-resource-grid">
        <RouterLink
          v-for="item in data.resources"
          :key="item.name"
          :to="`/admin/${item.name}`"
          class="card admin-resource"
          ><span>{{ item.label }}</span
          ><strong>{{ item.count }}</strong
          ><small
            >{{ item.readonly ? "查看与导出" : "管理与维护" }}
            <Icon name="arrow" :size="15" /></small
        ></RouterLink>
      </div>
      <section class="card section">
        <h2>报考数据概览</h2>
        <div class="application-status-grid">
          <div v-for="item in data.application_status" :key="item.status">
            <span>{{ zh(item.status) }}</span
            ><strong>{{ item.count }}</strong>
          </div>
          <p v-if="!data.application_status.length" class="muted">
            暂无报考记录。用户提交后可在报考数据管理中审核。
          </p>
        </div>
        <RouterLink to="/admin/applications" class="button primary"
          >进入报考数据管理 <Icon name="arrow" :size="17"
        /></RouterLink></section
    ></template>
  </div>
</template>
