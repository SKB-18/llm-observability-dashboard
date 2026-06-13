// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Cross-browser E2E tests for LLM Observability Dashboard.
 *
 * Prerequisites:
 *   1. Backend running:  uvicorn backend.main:app --port 8001
 *   2. Frontend running: cd frontend && npm run dev
 *   3. Install:          npx playwright install --with-deps
 *
 * Run:
 *   npx playwright test                        # all browsers
 *   npx playwright test --browser chromium     # single browser
 *   npx playwright test --ui                   # interactive UI mode
 */

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
});
