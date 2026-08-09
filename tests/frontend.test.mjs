// jsdom functional tests for index.html v2 (hardware-fit search + 7 hardware sections).
// Loads the real index.html + models/index.js via JSDOM.fromFile (file:// semantics:
// details render through models/bundle.js injection — no network, no fetch).
// Run: npm test   (also runs in the node CI container via make ci)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

async function boot() {
  const dom = await JSDOM.fromFile(join(ROOT, 'index.html'), {
    runScripts: 'dangerously',
    resources: 'usable',
    pretendToBeVisual: true,
  });
  const { window } = dom;
  await waitFor(() => window.MODELS_INDEX, 8000);
  assert.ok(window.MODELS_INDEX.length >= 14, 'expected >=14 sample models');
  return dom;
}

async function waitFor(fn, timeout = 4000, step = 25) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    try { const v = fn(); if (v) return v; } catch {}
    await new Promise((r) => setTimeout(r, step));
  }
  throw new Error('waitFor timed out');
}

function click(window, selector, index = 0) {
  const el = window.document.querySelectorAll(selector)[index];
  assert.ok(el, `no element for ${selector}[${index}]`);
  el.dispatchEvent(new window.Event('click', { bubbles: true }));
  return el;
}
function check(window, selector, checked) {
  const el = window.document.querySelector(selector);
  el.checked = checked;
  el.dispatchEvent(new window.Event('change', { bubbles: true }));
}
function input(window, selector, value) {
  const el = window.document.querySelector(selector);
  el.value = value;
  el.dispatchEvent(new window.Event('input', { bubbles: true }));
}
function change(window, selector, value) {
  const el = window.document.querySelector(selector);
  el.value = value;
  el.dispatchEvent(new window.Event('change', { bubbles: true }));
}
const boxes = (window, sel) => [...window.document.querySelectorAll(sel + ' .box')]
  .map((b) => ({ cls: b.className, txt: b.textContent }));
const cardCount = (window) => window.document.querySelectorAll('.card').length;

test('boot renders all sample cards with count', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  assert.equal(cardCount(window), window.MODELS_INDEX.length);
  assert.match(window.document.querySelector('#count').textContent, /14 models/);
  dom.window.close();
});

test('search filters the card list', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  const before = cardCount(window);
  input(window, '#search', 'Qwen');
  await waitFor(() => cardCount(window) < before);
  assert.ok(cardCount(window) > 0 && cardCount(window) < before);
  dom.window.close();
});

test('selecting a model renders 7 hardware sections with correct box counts', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  click(window, '.card');
  await waitFor(() => window.document.querySelector('#d-detail').style.display !== 'none', 6000);
  const h3s = [...window.document.querySelectorAll('#d-hw-sections h3')].map((h) => h.textContent);
  assert.equal(h3s.length, 7);
  assert.equal(window.document.querySelectorAll('#hw-nvidia .box').length, 5);
  assert.equal(window.document.querySelectorAll('#hw-amd .box').length, 4);
  assert.equal(window.document.querySelectorAll('#hw-macbook .box').length, 7);
  assert.equal(window.document.querySelectorAll('#hw-mac_studio .box').length, 7);
  assert.equal(window.document.querySelectorAll('#hw-dgx .box').length, 3);
  assert.equal(window.document.querySelectorAll('#hw-android .box').length, 4);
  assert.equal(window.document.querySelectorAll('#hw-iphone .box').length, 2);
  dom.window.close();
});

test('quant switch flips hardware boxes (70B: Q4_K_M vs Q8_0)', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  input(window, '#search', 'Llama 3.1 70B');
  await waitFor(() => cardCount(window) === 1);
  click(window, '.card');
  await waitFor(() => window.document.querySelector('#d-detail').style.display !== 'none', 6000);
  const nvidia = () => boxes(window, '#hw-nvidia');
  const q4 = nvidia();
  assert.ok(q4.some((b) => b.cls.includes('on')), 'Q4_K_M should fit at least one NVIDIA tier');
  click(window, '#d-quants .chip', 2); // Q8_0
  await waitFor(() => JSON.stringify(nvidia()) !== JSON.stringify(q4));
  const q8 = nvidia();
  assert.ok(q8.filter((b) => b.cls.includes('on')).length < q4.filter((b) => b.cls.includes('on')).length,
    'Q8_0 should enable fewer NVIDIA tiers than Q4_K_M');
  dom.window.close();
});

test('extreme MoE (DeepSeek-R1) shows no consumer NVIDIA but DGX green', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  input(window, '#search', 'DeepSeek-R1');
  await waitFor(() => cardCount(window) === 1);
  click(window, '.card');
  await waitFor(() => window.document.querySelector('#d-detail').style.display !== 'none', 6000);
  assert.equal(boxes(window, '#hw-nvidia').filter((b) => b.cls.includes('on')).length, 0);
  assert.ok(boxes(window, '#hw-dgx').filter((b) => b.cls.includes('on')).length >= 1);
  dom.window.close();
});

test('hardware-fit search: NVIDIA 12GB + only-fits filters cards and badges them', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  change(window, '#hwcat', 'nvidia');
  await waitFor(() => !window.document.querySelector('#hwtier').disabled);
  change(window, '#hwtier', '12');
  const before = cardCount(window);
  check(window, '#hwonly', true);
  await waitFor(() => cardCount(window) < before);
  const n = cardCount(window);
  assert.ok(n > 0, 'at least one model should fit a 12GB NVIDIA card');
  assert.equal(window.document.querySelectorAll('.card .fitbadge').length, n,
    'every filtered card must show the fits badge');
  dom.window.close();
});

test('file:// bundle path renders details without fetch (jsdom has no fetch on file:)', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  assert.equal(window.location.protocol, 'file:');
  click(window, '.card');
  await waitFor(() => window.document.querySelector('#d-detail').style.display !== 'none', 6000);
  assert.ok(window.document.querySelector('#d-name').textContent.length > 0);
  dom.window.close();
});
