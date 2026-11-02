import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: "http://127.0.0.1:4173/game516770/",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    launchOptions: {
      executablePath:
        process.env.CHROMIUM_PATH ||
        (process.env.CI ? undefined : "/usr/bin/chromium"),
      args: ["--no-sandbox"],
    },
  },
  webServer: {
    command: "npm run preview -- --port 4173 --host 127.0.0.1",
    url: "http://127.0.0.1:4173/game516770/",
    reuseExistingServer: !process.env.CI,
  },
  reporter: "list",
});
