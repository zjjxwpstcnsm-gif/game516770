import type { Event } from "./types";
export const shanghaiDate = (value: Date | string = new Date()) =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
export const formatTime = (value?: string | null) =>
  value && Number.isFinite(Date.parse(value))
    ? new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).format(new Date(value))
    : "未提供";
export const number = (value: unknown, digits = 2) =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString("zh-CN", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      })
    : "—";
export const percent = (value: unknown) =>
  typeof value === "number" && Number.isFinite(value)
    ? `${value > 0 ? "+" : ""}${(value * 100).toFixed(2)}%`
    : "—";
export const stale = (stamp?: string | null, now = Date.now(), hours = 36) =>
  !stamp ||
  !Number.isFinite(Date.parse(stamp)) ||
  now - Date.parse(stamp) > hours * 3600000;
export function upcoming(events: Event[], days: number, now = new Date()) {
  const start = shanghaiDate(now);
  const end = shanghaiDate(new Date(now.getTime() + days * 86400000));
  return events
    .filter(
      (e) =>
        e.event_date &&
        e.event_date.slice(0, 10) >= start &&
        e.event_date.slice(0, 10) <= end &&
        !["cancelled", "postponed", "completed", "rumored"].includes(e.status),
    )
    .sort((a, b) => (a.event_date || "").localeCompare(b.event_date || ""));
}
export const safeURL = (url?: string) => {
  try {
    const u = new URL(url || "");
    return ["https:", "http:"].includes(u.protocol) ? u.href : undefined;
  } catch {
    return undefined;
  }
};
export const describe = (x: unknown): string =>
  typeof x === "string"
    ? x
    : Array.isArray(x)
      ? x.map(describe).join("；")
      : x && typeof x === "object"
        ? Object.entries(x)
            .map(([k, v]) => `${k}：${describe(v)}`)
            .join("；")
        : x == null
          ? "暂无可核实数据"
          : String(x);
export const statusLabel = (s: string) =>
  ({
    confirmed: "已确认",
    production_build_passed: "生产构建已通过",
    not_run: "尚未执行",
    announced: "已公布",
    completed: "已发生",
    rumored: "传闻",
    postponed: "已延期",
    cancelled: "已取消",
    verified: "已核实",
    unverified: "待核验",
    success: "正常",
    ok: "正常",
    partial: "部分降级",
    partial_failure: "部分采集降级",
    insufficient_samples: "样本不足",
    failed: "失败",
    unavailable: "不可用",
    disabled: "未启用",
    missing_key: "未配置密钥",
    not_configured: "未配置",
    skipped: "已跳过",
  })[s] || s;
