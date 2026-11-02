import { describe, it, expect } from "vitest";
import {
  upcoming,
  stale,
  safeURL,
  shanghaiDate,
  percent,
  number,
} from "./utils";
import type { Event } from "./types";
const event = (date: string, status = "confirmed"): Event => ({
  id: date,
  game_id: "game",
  title: "event",
  type: "release",
  importance: "SS",
  event_date: date,
  status,
  source_urls: [],
});
describe("事件时间与安全展示", () => {
  it("按北京时间跨 UTC 日期", () =>
    expect(shanghaiDate("2026-11-01T20:00:00Z")).toBe("2026-11-02"));
  it("7 天与 30 天真实事件筛选", () => {
    const list = [
      event("2026-11-03"),
      event("2026-11-12"),
      event("2026-11-05", "rumored"),
      event("2026-11-04", "cancelled"),
      event("2026-10-30"),
    ];
    expect(
      upcoming(list, 7, new Date("2026-11-02T00:00:00+08:00")),
    ).toHaveLength(1);
    expect(
      upcoming(list, 30, new Date("2026-11-02T00:00:00+08:00")),
    ).toHaveLength(2);
  });
  it("缺失与过期时间暂停判断", () => {
    expect(stale(null)).toBe(true);
    expect(stale("bad-date")).toBe(true);
    expect(
      stale("2026-11-01T00:00:00Z", Date.parse("2026-11-03T00:00:00Z")),
    ).toBe(true);
  });
  it("拒绝脚本或非法来源链接", () => {
    expect(safeURL("javascript:alert(1)")).toBeUndefined();
    expect(safeURL("https://example.com")).toBe("https://example.com/");
  });
  it("缺失数字绝不展示为零", () => {
    expect(number(null)).toBe("—");
    expect(percent(undefined)).toBe("—");
    expect(percent(0)).toBe("0.00%");
    expect(percent(0.012)).toBe("+1.20%");
  });
});
