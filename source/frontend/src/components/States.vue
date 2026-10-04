<script setup>
import Icon from "./Icon.vue";
defineProps({
  loading: Boolean,
  error: String,
  empty: Boolean,
  text: { type: String, default: "这里还没有记录" },
});
defineEmits(["retry"]);
</script>
<template>
  <div v-if="loading" class="skeleton-grid" role="status" aria-label="正在加载">
    <div v-for="i in 3" :key="i" class="skeleton"><span /><span /><span /></div>
    <span class="sr-only">正在读取本地数据</span>
  </div>
  <div v-else-if="error" class="empty error">
    <Icon name="alert" :size="36" />
    <h3>暂时无法加载</h3>
    <p>{{ error }}</p>
    <button class="button" @click="$emit('retry')">重新加载</button>
  </div>
  <div v-else-if="empty" class="empty">
    <Icon name="layers" :size="36" />
    <h3>{{ text }}</h3>
    <p>试试调整筛选条件，或添加第一条记录。</p>
    <slot />
  </div>
</template>
