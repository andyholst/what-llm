import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  fullyParallel: false,   // serial: deterministic and kind to constrained environments
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:8124',
    headless: true,
    chromiumSandbox: false,
    viewport: { width: 1280, height: 800 },
  },
  webServer: {
    command: 'node tests/e2e/serve.mjs 8124',
    port: 8124,
    reuseExistingServer: true,
  },
});
