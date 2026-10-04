import { reactive } from "vue";
let persisted;
try {
  persisted = JSON.parse(sessionStorage.getItem("exam-session") || "null");
} catch {
  persisted = null;
}
export const session = reactive({
  access: persisted?.access || "",
  refresh: persisted?.refresh || "",
  user: persisted?.user || null,
});
export const ui = reactive({ busy: 0, toasts: [] });
export function saveSession(value) {
  Object.assign(session, value);
  if (value.user) sessionStorage.setItem("exam-session", JSON.stringify(value));
  else sessionStorage.removeItem("exam-session");
}
export function toast(message, type = "success") {
  const id = Date.now() + Math.random();
  ui.toasts.push({ id, message, type });
  setTimeout(() => {
    ui.toasts = ui.toasts.filter((t) => t.id !== id);
  }, 5500);
}
export function errorText(value) {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(errorText).join("；");
  if (value && typeof value === "object")
    return Object.entries(value)
      .map(([k, v]) => `${k}: ${errorText(v)}`)
      .join("；");
  return String(value || "请求失败");
}
let refreshJob;
async function refreshSession() {
  if (!refreshJob)
    refreshJob = (async () => {
      const res = await fetch("/api/v1/auth/refresh/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: session.refresh }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error("登录已过期，请重新登录。");
      saveSession(data.data);
    })().finally(() => {
      refreshJob = null;
    });
  return refreshJob;
}
export async function api(path, options = {}, retry = true) {
  ui.busy++;
  try {
    const headers = {
      ...(session.access ? { Authorization: `Bearer ${session.access}` } : {}),
    };
    if (options.body && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
      options = {
        ...options,
        body:
          typeof options.body === "string"
            ? options.body
            : JSON.stringify(options.body),
      };
    }
    const res = await fetch(`/api/v1/${path}`, {
      ...options,
      headers: { ...headers, ...options.headers },
    });
    if (
      res.status === 401 &&
      retry &&
      session.refresh &&
      !path.startsWith("auth/")
    ) {
      try {
        await refreshSession();
        return await api(path, options, false);
      } catch (e) {
        saveSession({ access: "", refresh: "", user: null });
        window.dispatchEvent(new Event("session-expired"));
        throw e;
      }
    }
    if (options.download) {
      if (!res.ok) {
        const error = await res.json();
        throw new Error(errorText(error.errors || error.message));
      }
      const url = URL.createObjectURL(await res.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = options.filename || "export.xlsx";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      return;
    }
    if (res.status === 204) return null;
    const value = await res.json();
    if (!res.ok || value.success === false)
      throw new Error(errorText(value.errors || value.message));
    return value.data;
  } finally {
    ui.busy--;
  }
}
export const get = (path) => api(path);
export const post = (path, body) => api(path, { method: "POST", body });
export const patch = (path, body) => api(path, { method: "PATCH", body });
export const remove = (path) => api(path, { method: "DELETE" });
export async function act(fn, message) {
  try {
    const result = await fn();
    if (message) toast(message);
    return result;
  } catch (e) {
    toast(e.message, "error");
    return null;
  }
}
export function query(values) {
  return new URLSearchParams(
    Object.entries(values).filter(
      ([, v]) => v !== "" && v !== null && v !== undefined,
    ),
  ).toString();
}
