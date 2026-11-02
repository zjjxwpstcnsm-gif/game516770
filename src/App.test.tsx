import React from "react";
import {
  render,
  screen,
  cleanup,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, describe, it, expect, vi } from "vitest";
import App from "./App";
const fixture = {
  schema_version: "1.0",
  generated_at: new Date().toISOString(),
  timezone: "Asia/Shanghai",
  news: [],
  games: [],
  events: [],
  etfs: [],
  signals: [],
  report: {},
  system: { status: "partial", strategy_version: "test", source_status: [] },
  event_studies: [],
  backtest: { status: "unavailable" },
};
beforeEach(() => {
  window.location.hash = "#/dashboard";
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => fixture }),
  );
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      disconnect() {}
      unobserve() {}
    },
  );
  vi.spyOn(window, "scrollTo").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
describe("真实数据页面状态", () => {
  it("显示加载态、空行情以及暂停判断", async () => {
    render(<App />);
    expect(screen.getByText("正在读取研究数据")).toBeInTheDocument();
    await screen.findByText("ETF 行情尚未采集");
    expect(screen.getByText("数据不足，暂停判断")).toBeInTheDocument();
  });
  it("错误数据可重试且不伪造市场数据", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 503 }),
    );
    render(<App />);
    await screen.findByText("研究数据暂不可用");
    fireEvent.click(screen.getByRole("button", { name: /^重新加载$/ }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  });
  it("过期快照显示明显警告", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ...fixture,
          generated_at: "2020-01-01T00:00:00Z",
        }),
      }),
    );
    render(<App />);
    await screen.findByText(/当前为过期历史快照/);
    expect(screen.getByText("数据已过期，暂停判断")).toBeInTheDocument();
  });
  it("日历空状态和 7/30/90 日交互", async () => {
    window.location.hash = "#/calendar";
    render(<App />);
    await screen.findByText("暂无已确认的重大事件");
    for (const days of [7, 30, 90]) {
      fireEvent.click(screen.getByRole("button", { name: `未来 ${days} 天` }));
      expect(
        screen.getByRole("button", { name: `未来 ${days} 天` }),
      ).toHaveClass("selected");
    }
    fireEvent.click(screen.getByRole("button", { name: "月历" }));
    expect(document.querySelector(".calendar-grid")).toBeInTheDocument();
  });
  it("使用 GitHub Pages 项目资源路径", async () => {
    render(<App />);
    await screen.findByText("ETF 行情尚未采集");
    expect(vi.mocked(fetch).mock.calls[0][0]).toMatch(/data\/latest.json$/);
  });
});
