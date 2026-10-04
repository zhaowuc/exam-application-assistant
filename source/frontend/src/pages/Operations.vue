<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { get, post, api, act, saveSession } from "../api";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
const router = useRouter(),
  backups = ref([]),
  loading = ref(true),
  error = ref(""),
  health = ref(null),
  file = ref(null),
  busy = ref(false);
async function load() {
  loading.value = true;
  try {
    [backups.value, health.value] = await Promise.all([
      get("admin/backups/"),
      get("health/"),
    ]);
    error.value = "";
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
async function backup() {
  busy.value = true;
  const result = await act(
    () => post("admin/backups/", {}),
    "备份已保存在本机",
  );
  if (result) load();
  busy.value = false;
}
async function restore(event) {
  const f = event.target.files[0];
  if (!f) return;
  if (
    !confirm(
      "恢复将替换当前数据，并退出全部登录。系统会先保存当前数据的安全备份。是否继续？",
    )
  ) {
    event.target.value = "";
    return;
  }
  busy.value = true;
  const body = new FormData();
  body.append("file", f);
  body.append("confirm", "RESTORE");
  const result = await act(
    () => api("admin/restore/", { method: "POST", body }),
    "恢复成功，请重新登录",
  );
  event.target.value = "";
  if (result) {
    saveSession({ access: "", refresh: "", user: null });
    router.push("/login");
  }
  busy.value = false;
}
onMounted(load);
</script>
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">YOUR DATA, YOUR CONTROL</div>
        <h1>系统运行</h1>
        <p>检查本地服务状态，安全备份与恢复应用数据。</p>
      </div>
      <button class="button" @click="load">
        <Icon name="refresh" :size="17" />刷新状态
      </button>
    </div>
    <States :loading="loading" :error="error" @retry="load" /><template
      v-if="health"
      ><div class="stats-grid">
        <div class="stat-card">
          <span class="stat-icon teal"><Icon name="success" /></span>
          <div>
            <p>本地服务</p>
            <strong class="word-stat">运行正常</strong
            ><span>数据库连接已检查</span>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon blue"><Icon name="admin" /></span>
          <div>
            <p>运行模式</p>
            <strong class="word-stat">离线本机</strong
            ><span>仅监听 127.0.0.1</span>
          </div>
        </div>
        <div class="stat-card">
          <div>
            <p>应用版本</p>
            <strong class="word-stat">{{ health.version }}</strong
            ><span>Django + Vue 重构版</span>
          </div>
        </div>
      </div></template
    >
    <section class="card section backup-card">
      <div class="section-heading">
        <div>
          <h2>数据备份</h2>
          <p>备份包含用户资料、题库、答题记录和报考数据，请妥善保管。</p>
        </div>
        <button class="button primary" :disabled="busy" @click="backup">
          <Icon name="plus" :size="17" />创建备份
        </button>
      </div>
      <div v-for="row in backups" :key="row.filename" class="backup-row">
        <Icon name="file" :size="21" />
        <div>
          <strong>{{ row.filename }}</strong
          ><small>{{ (row.size / 1024 / 1024).toFixed(2) }} MB</small>
        </div>
        <button
          class="button small"
          @click="
            act(() =>
              api(`admin/backups/${row.filename}/`, {
                download: true,
                filename: row.filename,
              }),
            )
          "
        >
          <Icon name="download" :size="15" />下载
        </button>
      </div>
      <p v-if="!backups.length" class="muted">尚未创建备份。</p>
    </section>
    <section class="card section restore-card">
      <h2>恢复数据</h2>
      <p class="muted">
        仅接受与当前数据结构兼容的 SQLite
        备份。恢复前自动创建安全备份；恢复后所有账号需重新登录。
      </p>
      <button class="button danger" :disabled="busy" @click="file.click()">
        <Icon name="upload" :size="17" />选择数据库备份并恢复</button
      ><input
        ref="file"
        type="file"
        accept=".sqlite3,.db"
        hidden
        @change="restore"
      />
    </section>
    <div class="callout section">
      数据位置：交付包内 data/db.sqlite3。移动程序时请移动整个文件夹；不要删除
      data 文件夹。退出启动器才会关闭本地服务。
    </div>
  </div>
</template>
