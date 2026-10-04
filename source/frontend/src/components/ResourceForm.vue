<script setup>
import { ref } from "vue";
import { fieldLabels } from "../labels";
const props = defineProps({ fields: Array, initial: Object, busy: Boolean });
const emit = defineEmits(["save"]);
const values = ref({}),
  error = ref("");
for (const field of props.fields) {
  let value = props.initial?.[field.key];
  if (field.type === "json")
    value = value === undefined ? "" : JSON.stringify(value, null, 2);
  else if (field.type === "datetime")
    value = value
      ? new Date(
          new Date(value).getTime() -
            new Date(value).getTimezoneOffset() * 60000,
        )
          .toISOString()
          .slice(0, 16)
      : "";
  values.value[field.key] = value ?? (field.type === "boolean" ? false : "");
}
function submit() {
  error.value = "";
  try {
    const output = {};
    for (const field of props.fields) {
      let value = values.value[field.key];
      if (value === "" && (field.key === "password" || field.key === "detail"))
        continue;
      if (value === "" && !field.required && !props.initial) continue;
      if (value === "" && field.nullable) value = null;
      else if (field.type === "json") {
        if (value === "") continue;
        value = JSON.parse(value);
      } else if (
        ["integer", "number", "relation"].includes(field.type) &&
        value !== null &&
        value !== ""
      )
        value = Number(value);
      else if (field.type === "datetime" && value)
        value = new Date(value).toISOString();
      output[field.key] = value;
    }
    emit("save", output);
  } catch (e) {
    error.value = "JSON格式不正确，请检查引号、逗号和括号。";
  }
}
</script>
<template>
  <form @submit.prevent="submit" class="form-stack">
    <div class="form-grid">
      <label
        v-for="field in fields"
        :key="field.key"
        :class="{
          'full-width': ['json', 'textarea'].includes(field.type),
          'checkbox-label': field.type === 'boolean',
        }"
      >
        <template v-if="field.type === 'boolean'">
          <input
            v-model="values[field.key]"
            type="checkbox"
            :aria-label="fieldLabels[field.key] || field.label"
          />{{ fieldLabels[field.key] || field.label }}
        </template>
        <template v-else>
          <span
            >{{ fieldLabels[field.key] || field.label }}
            <span v-if="field.required" class="required" aria-hidden="true"
              >*</span
            ></span
          >
          <select
            v-if="field.type === 'choice' || field.type === 'relation'"
            v-model="values[field.key]"
            :required="field.required"
            :aria-label="fieldLabels[field.key] || field.label"
          >
            <option
              v-if="(!initial && !field.required) || field.nullable"
              :value="field.nullable ? null : ''"
            >
              不设置
            </option>
            <option
              v-for="option in field.choices || field.options"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
          <textarea
            v-else-if="['json', 'textarea'].includes(field.type)"
            v-model="values[field.key]"
            :required="field.required"
            :rows="field.type === 'json' ? 3 : 4"
            :class="{ 'code-input': field.type === 'json' }"
            :placeholder="
              field.type === 'json' ? '填写有效 JSON；留空使用默认值' : ''
            "
            :aria-label="fieldLabels[field.key] || field.label"
          />
          <input
            v-else
            v-model="values[field.key]"
            :type="
              {
                integer: 'number',
                number: 'number',
                date: 'date',
                datetime: 'datetime-local',
                password: 'password',
              }[field.type] || 'text'
            "
            :required="field.required && !(initial && field.key === 'password')"
            :step="
              field.type === 'integer'
                ? 1
                : field.type === 'number'
                  ? 'any'
                  : undefined
            "
            :maxlength="field.max_length || undefined"
            :autocomplete="
              field.key === 'password' ? 'new-password' : undefined
            "
            :aria-label="fieldLabels[field.key] || field.label"
          />
        </template>
      </label>
    </div>
    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <button class="button primary" :disabled="busy">
      {{ busy ? "正在保存…" : "保存记录" }}
    </button>
  </form>
</template>
