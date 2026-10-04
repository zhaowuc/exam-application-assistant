<script setup>
import { onMounted, onBeforeUnmount, ref, nextTick } from "vue";
import Icon from "./Icon.vue";
defineProps({ title: String, wide: Boolean });
const emit = defineEmits(["close"]);
const panel = ref();
const original = document.activeElement;
function key(e) {
  if (e.key === "Escape") emit("close");
  if (e.key === "Tab") {
    const els = [
      ...panel.value.querySelectorAll("button,input,textarea,select,a[href]"),
    ].filter((el) => !el.disabled && el.offsetParent !== null);
    const first = els[0],
      last = els.at(-1);
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last?.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first?.focus();
    }
  }
}
onMounted(async () => {
  document.body.style.overflow = "hidden";
  window.addEventListener("keydown", key);
  await nextTick();
  panel.value.querySelector("input,textarea,select,button")?.focus();
});
onBeforeUnmount(() => {
  document.body.style.overflow = "";
  window.removeEventListener("keydown", key);
  original?.focus();
});
</script>
<template>
  <Teleport to="body"
    ><div class="modal-backdrop" @mousedown.self="$emit('close')">
      <section
        ref="panel"
        class="modal"
        :class="{ wide }"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
      >
        <header>
          <h2>{{ title }}</h2>
          <button
            class="icon-button"
            @click="$emit('close')"
            aria-label="关闭对话框"
          >
            <Icon name="close" />
          </button>
        </header>
        <div class="modal-content"><slot /></div>
      </section></div
  ></Teleport>
</template>
