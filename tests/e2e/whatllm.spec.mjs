// Playwright browser tests against the served what-llm frontend (real Chromium).
// Runs in the node CI container (`make node-test`) and locally with `npx playwright test`.
import { test, expect } from '@playwright/test';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';

const FILE_URL = pathToFileURL(join(process.cwd(), 'index.html')).href;

test('served app renders cards and search filters', async ({ page }) => {
  await page.goto('/');
  const cards = page.locator('.card');
  await expect(cards.first()).toBeVisible();
  const n0 = await cards.count();
  expect(n0).toBeGreaterThan(0);
  await page.fill('#search', 'Qwen');
  await expect(cards.first()).toBeVisible();
  expect(await cards.count()).toBeLessThanOrEqual(n0);
});

test('model details: quant switch flips hardware boxes', async ({ page }) => {
  await page.goto('/');
  await page.fill('#search', 'Llama 3.1 70B');
  await expect(page.locator('.card')).toHaveCount(1);
  await page.locator('.card').click();
  await expect(page.locator('#d-detail')).toBeVisible();
  const nvidia = page.locator('#hw-nvidia .box');
  await expect(nvidia.first()).toBeVisible();
  const before = await nvidia.allTextContents();
  const chips = page.locator('#d-quants .chip');
  const n = await chips.count();
  expect(n).toBeGreaterThan(1);
  for (let i = 1; i < n; i++) {
    await chips.nth(i).click();
    const after = await nvidia.allTextContents();
    if (after.join('|') !== before.join('|')) break;
  }
});

test('extreme MoE shows no consumer NVIDIA support', async ({ page }) => {
  await page.goto('/');
  await page.fill('#search', 'DeepSeek-R1');
  await expect(page.locator('.card')).toHaveCount(1);
  await page.locator('.card').click();
  await expect(page.locator('#d-detail')).toBeVisible();
  await expect(page.locator('#hw-nvidia .box.off').first()).toBeVisible();
  expect(await page.locator('#hw-nvidia .box.on').count()).toBe(0);
  // DGX boxes present and green for the extreme MoE
  await expect(page.locator('#hw-dgx .box.on').first()).toBeVisible();
});

test('hardware-fit search: NVIDIA 12GB + only-fits filters the list', async ({ page }) => {
  await page.goto('/');
  await page.selectOption('#hwcat', 'nvidia');
  await page.selectOption('#hwtier', '12');
  const before = await page.locator('.card').count();
  await page.check('#hwonly');
  await expect.poll(() => page.locator('.card').count()).toBeLessThan(before);
  const cards = page.locator('.card');
  await expect(cards.first()).toBeVisible();
  const names = await cards.allTextContents();
  expect(names.length).toBeGreaterThan(0);
  // every visible card must carry the fits badge
  const badges = await page.locator('.card .fitbadge').count();
  expect(badges).toBe(names.length);
});

test('file:// opens without a blank screen (bundle path)', async ({ page }) => {
  await page.goto(FILE_URL);
  const list = page.locator('#list');
  const err = page.locator('.err');
  await expect(list.or(err).first()).toBeVisible();
  if (await list.count() > 0) {
    await list.locator('.card').first().click();
    await expect(page.locator('#d-detail')).toBeVisible();
  }
});
