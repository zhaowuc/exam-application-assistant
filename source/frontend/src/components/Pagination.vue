<script setup>
import Icon from "./Icon.vue";
defineProps({
  page: Number,
  count: Number,
  size: { type: Number, default: 12 },
});
defineEmits(["change"]);
</script>
<template>
  <div v-if="count" class="pagination">
    <span
      >共 {{ count }} 条 · 第 {{ page }} /
      {{ Math.ceil(count / size) }} 页</span
    >
    <div>
      <button
        class="icon-button"
        aria-label="上一页"
        :disabled="page <= 1"
        @click="$emit('change', page - 1)"
      >
        <Icon name="left" /></button
      ><button
        class="icon-button"
        aria-label="下一页"
        :disabled="page >= Math.ceil(count / size)"
        @click="$emit('change', page + 1)"
      >
        <Icon name="right" />
      </button>
    </div>
  </div>
</template>
