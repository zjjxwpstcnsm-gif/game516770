import { test, expect } from "@playwright/test";
const pages = [
  "dashboard",
  "calendar",
  "games",
  "etf",
  "signals",
  "backtest",
  "news",
  "system",
];
for (const width of [1440, 390])
  test(`所有研究页面可访问，${width}px 无横向溢出`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    for (const route of pages) {
      await page.goto(`#/${route}`);
      await expect(page.locator("main h1")).toBeVisible();
      await expect(page.getByText("正在读取研究数据")).toHaveCount(0);
      await expect(page.locator("main .error-panel")).toHaveCount(0);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBe(true);
    }
    await page.goto("#/dashboard");
    await page.screenshot({
      path: `test-results/dashboard-${width}.png`,
      fullPage: true,
    });
    expect(errors).toEqual([]);
  });
test("过期快照暂停今日信号", async ({ page }) => {
  await page.route("**/data/latest.json", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.generated_at = "2020-01-01T00:00:00+08:00";
    await route.fulfill({ json: data });
  });
  await page.goto("#/dashboard");
  await expect(
    page.getByText("当前为过期历史快照", { exact: false }),
  ).toBeVisible();
  await expect(page.getByText("数据已过期，暂停判断")).toBeVisible();
});
test("空数据和加载失败可见且可重试", async ({ page }) => {
  await page.route("**/data/latest.json", (route) =>
    route.fulfill({
      json: {
        schema_version: "1.0",
        generated_at: new Date().toISOString(),
        timezone: "Asia/Shanghai",
        news: [],
        games: [],
        events: [],
        etfs: [],
        signals: [],
        report: {},
        system: {
          status: "partial",
          strategy_version: "test",
          source_status: [],
        },
        event_studies: [],
        backtest: { status: "unavailable" },
      },
    }),
  );
  await page.goto("#/calendar");
  await expect(page.getByText("暂无已确认的重大事件")).toBeVisible();
  await page.unroute("**/data/latest.json");
  await page.route("**/data/latest.json", (route) =>
    route.fulfill({ status: 503, body: "Unavailable" }),
  );
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "研究数据暂不可用" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "重新加载", exact: true }),
  ).toBeVisible();
});
test("游戏详情与 ETF 图表", async ({ page }) => {
  await page.goto("#/games");
  const first = page.locator(".game-card").first();
  await expect(first).toBeVisible();
  await first.click();
  await expect(
    page.getByRole("heading", { name: "完整事件里程碑" }),
  ).toBeVisible();
  await page.goto("#/etf");
  await expect(page.locator(".recharts-surface").first()).toBeVisible();
});
