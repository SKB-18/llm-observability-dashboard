// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Cross-browser E2E tests for the LLM Observability Dashboard.
 * Requires backend (port 8001) and frontend (port 5173) to be running.
 */

test.describe('Dashboard loads', () => {
  test('page title is visible', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/LLM/i);
  });

  test('header shows LLM Observability Dashboard', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText(/LLM Observability/i).first()).toBeVisible();
  });

  test('metrics cards are present', async ({ page }) => {
    await page.goto('/');
    // Wait for the summary to load (cards appear after API fetch)
    await page.waitForSelector('[data-testid="metrics-card"], .rounded-2xl', { timeout: 10_000 });
    const cards = page.locator('.rounded-2xl');
    await expect(cards.first()).toBeVisible();
  });
});

test.describe('Source filter', () => {
  test('LMSYS and Evals filter buttons exist', async ({ page }) => {
    await page.goto('/');
    // Source filter tabs
    const lmsys = page.getByText(/lmsys/i).first();
    const evals = page.getByText(/evals/i).first();
    await expect(lmsys).toBeVisible();
    await expect(evals).toBeVisible();
  });

  test('clicking LMSYS filter does not crash the page', async ({ page }) => {
    await page.goto('/');
    const lmsys = page.getByText(/lmsys/i).first();
    await lmsys.click();
    // Page should still be alive
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Charts are rendered', () => {
  test('recharts SVG elements are present', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000); // allow data to load
    const svgs = page.locator('svg.recharts-surface');
    const count = await svgs.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Completions table', () => {
  test('completions table section is visible', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    // Table or "no data" message
    const table = page.locator('table, [data-testid="completions-table"]');
    const noData = page.getByText(/no completions|no data/i);
    const visible = (await table.count()) > 0 || (await noData.count()) > 0;
    expect(visible).toBe(true);
  });
});

test.describe('Upload section', () => {
  test('upload dataset section is visible', async ({ page }) => {
    await page.goto('/');
    // Look for Upload Your Dataset heading
    const heading = page.getByText(/upload your dataset/i);
    await expect(heading).toBeVisible({ timeout: 10_000 });
  });

  test('drag-drop zone is present', async ({ page }) => {
    await page.goto('/');
    const dropzone = page.locator('[data-testid="dropzone"], .border-dashed').first();
    await expect(dropzone).toBeVisible({ timeout: 10_000 });
  });
});

test.describe('API connectivity', () => {
  test('backend health endpoint responds 200', async ({ request }) => {
    const resp = await request.get('http://localhost:8001/health');
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.status).toBe('ok');
  });

  test('metrics summary API returns expected shape', async ({ request }) => {
    const resp = await request.get('http://localhost:8001/api/v1/metrics/summary');
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body).toHaveProperty('total_requests');
  });
});

test.describe('Responsive layout', () => {
  test('dashboard is usable on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 }); // iPhone 14
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
    // No horizontal scrollbar (max-width fits)
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyWidth).toBeLessThanOrEqual(viewWidth + 5); // 5px tolerance
  });

  test('dashboard is usable on wide desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
  });
});
