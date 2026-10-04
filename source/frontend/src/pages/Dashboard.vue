<script setup>
import { ref, onMounted } from "vue";
import { get, session } from "../api";
import { zh, date } from "../labels";
import Icon from "../components/Icon.vue";
import States from "../components/States.vue";
const data = ref(null),
  error = ref(""),
  loading = ref(true);
async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await get("home/");
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
        <div class="eyebrow">YOUR PERSONAL WORKSPACE</div>
        <h1>{{ session.user?.username }}，从这里开始。</h1>
        <p>把目标看清，把准备做实。你的备考进展，都在这里。</p>
      </div>
      <span class="date-chip"
        ><Icon name="clock" :size="16" />{{
          new Date().toLocaleDateString("zh-CN", {
            month: "long",
            day: "numeric",
            weekday: "long",
          })
        }}</span
      >
    </div>
    <States :loading="loading" :error="error" @retry="load" /><template
      v-if="data"
      ><section class="dashboard-hero">
        <div class="hero-copy">
          <span class="hero-kicker">清晰的目标，是好的开始</span>
          <h2>下一站，<br />由你选择。</h2>
          <p>
            从公务员、事业单位到研究生，<br />用完整档案发现更适合你的方向。
          </p>
          <RouterLink to="/recommendations" class="button white"
            >发现我的方向 <Icon name="arrow" :size="17"
          /></RouterLink>
        </div>
        <div class="hero-art" aria-hidden="true">
          <div class="art-halo" />
          <div class="art-ring" />
          <div class="art-panel panel-back"><span /><span /><span /></div>
          <div class="art-panel panel-front">
            <div class="art-icon"><Icon name="brand" :size="44" /></div>
            <span class="art-line" /><span class="art-line short" />
            <div class="art-chart"><i /><i /><i /><i /><i /></div>
            <div class="art-check"><Icon name="check" :size="21" /></div>
          </div>
          <div class="art-floating">
            <Icon name="success" :size="21" /><span>每一步，都有方向</span>
          </div>
        </div>
        <span class="hero-watermark">NEXT</span>
      </section>
      <div class="stats-grid">
        <RouterLink to="/catalog/civil" class="stat-card"
          ><span class="stat-icon teal"><Icon name="civil" /></span>
          <div>
            <p>可探索报考目标</p>
            <strong>{{ data.counts.opportunities }}</strong
            ><span>条本地招考记录</span>
          </div>
          <Icon name="up" class="stat-arrow" :size="18" /></RouterLink
        ><RouterLink to="/practice" class="stat-card"
          ><span class="stat-icon blue"><Icon name="practice" /></span>
          <div>
            <p>离线精选题库</p>
            <strong>{{ data.counts.questions }}</strong
            ><span>道题，循序积累</span>
          </div>
          <Icon name="up" class="stat-arrow" :size="18" /></RouterLink
        ><RouterLink to="/services" class="stat-card"
          ><span class="stat-icon amber"><Icon name="services" /></span>
          <div>
            <p>公共服务指南</p>
            <strong>{{ data.counts.services }}</strong
            ><span>项办事与材料指引</span>
          </div>
          <Icon name="up" class="stat-arrow" :size="18"
        /></RouterLink>
      </div>
      <section class="section">
        <div class="section-heading">
          <div>
            <h2>三条路径，同一个未来</h2>
            <p>选择你感兴趣的方向，查看招录条件与历年数据。</p>
          </div>
        </div>
        <div class="path-grid">
          <RouterLink
            v-for="(type, i) in ['civil', 'institution', 'graduate']"
            :key="type"
            :to="`/catalog/${type}`"
            class="path-card"
            :class="`path-${i}`"
            ><span class="path-index">0{{ i + 1 }}</span
            ><Icon :name="type" :size="30" />
            <h3>{{ zh(type) }}报考</h3>
            <p>
              {{
                [
                  "公共事务与服务的起点",
                  "发挥专业价值的广阔空间",
                  "继续探索知识的更深处",
                ][i]
              }}
            </p>
            <span>探索方向 <Icon name="arrow" :size="17" /></span
          ></RouterLink>
        </div>
      </section>
      <div class="dashboard-bottom">
        <section class="card">
          <div class="section-heading">
            <h2>公告与提醒</h2>
            <RouterLink to="/notices" class="text-link"
              >查看全部 <Icon name="arrow" :size="15"
            /></RouterLink>
          </div>
          <RouterLink
            v-for="notice in data.notices"
            :key="notice.id"
            to="/notices"
            class="notice-row"
            ><span class="notice-symbol"><Icon name="file" :size="19" /></span>
            <div>
              <strong>{{ notice.title }}</strong
              ><span
                >{{ zh(notice.exam_type) }} ·
                {{ date(notice.published_at) }}</span
              >
            </div>
            <Icon name="right" :size="18"
          /></RouterLink>
          <p v-if="!data.notices.length" class="muted">暂无公告</p>
        </section>
        <section class="card next-step">
          <span class="eyebrow">SMALL STEPS, REAL PROGRESS</span>
          <h2>做好今天的<br />一小步。</h2>
          <p>完善档案，让推荐更有依据。<br />练习一组题目，让进步有迹可循。</p>
          <RouterLink to="/profile" class="step-link"
            ><span>完善个人档案</span><Icon name="arrow" /></RouterLink
          ><RouterLink to="/practice" class="step-link"
            ><span>开始一次练习</span><Icon name="arrow" /></RouterLink
          ><RouterLink to="/applications" class="step-link"
            ><span>查看报考计划</span><Icon name="arrow"
          /></RouterLink>
        </section>
      </div>
      <p class="data-note">
        <Icon name="alert" :size="15" />{{ data.disclaimer }}
      </p></template
    >
  </div>
</template>
