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
  // pre-inject the bundle so card clicks never start a pending script load that
  // window.close() aborts (flaky unhandled-rejection in slow CI containers)
  if (!window.MODELS_BUNDLE) {
    await new Promise((resolve) => {
      const s = window.document.createElement('script');
      s.src = 'models/bundle.js';
      s.onload = resolve; s.onerror = resolve;
      window.document.head.appendChild(s);
    });
    await waitFor(() => window.MODELS_BUNDLE, 8000);
  }
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
  assert.match(window.document.querySelector('#count').textContent, /15 models/);
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
  assert.equal(h3s.length, 11);
  assert.equal(window.document.querySelectorAll('#hw-nvidia .box').length, 8);
  assert.equal(window.document.querySelectorAll('#hw-amd .box').length, 8);
  assert.equal(window.document.querySelectorAll('#hw-intel_arc .box').length, 4);
  assert.equal(window.document.querySelectorAll('#hw-snapdragon .box').length, 3);
  assert.equal(window.document.querySelectorAll('#hw-macbook .box').length, 7);
  assert.equal(window.document.querySelectorAll('#hw-mac_mini .box').length, 6);
  assert.equal(window.document.querySelectorAll('#hw-mac_studio .box').length, 7);
  assert.equal(window.document.querySelectorAll('#hw-mac_pro .box').length, 3);
  assert.equal(window.document.querySelectorAll('#hw-dgx .box').length, 3);
  assert.equal(window.document.querySelectorAll('#hw-android .box').length, 4);
  assert.equal(window.document.querySelectorAll('#hw-iphone .box').length, 2);
  // backend criteria labels visible (CUDA / ROCm / SYCL+Vulkan / Metal ...)
  assert.ok(h3s[0].includes('CUDA') && h3s[1].includes('ROCm') && h3s[2].includes('SYCL'),
    'backend labels on section headers: ' + h3s.join(' | '));
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

test('profile panel renders strengths/weaknesses/limitations with provenance', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  click(window, '.card');
  await waitFor(() => window.document.querySelector('#d-detail').style.display !== 'none', 6000);
  assert.ok(window.document.querySelector('#d-summary').textContent.length > 0, 'summary present');
  assert.ok(window.document.querySelectorAll('#d-strengths li').length > 0, 'strengths listed');
  const li = window.document.querySelector('#d-strengths li');
  assert.ok((li.title || '').includes('source:'), 'claim carries provenance in title');
  assert.ok(window.document.querySelector('#d-meta').textContent.includes('License'), 'license badge');
  dom.window.close();
});

test('commercial-only filter excludes non-commercial models', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  const before = cardCount(window);
  check(window, '#fcommercial', true);
  await waitFor(() => cardCount(window) < before);
  assert.ok(cardCount(window) > 0);
  const names = [...window.document.querySelectorAll('.card .nm')].map(e => e.textContent);
  assert.ok(!names.some(n => n.includes('Dolphin')), 'dolphin (CC-BY-NC) filtered out');
  dom.window.close();
});

test('model-type filter narrows to reasoner models', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  change(window, '#ftype', 'reasoner');
  await waitFor(() => cardCount(window) > 0);
  const rows = [...window.document.querySelectorAll('.card')];
  assert.ok(rows.length >= 1 && rows.length < 15, 'subset shown');
  dom.window.close();
});

test('use-case filter matches best_for chips', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  const opts = [...window.document.querySelector('#fuse').options].map(o => o.value);
  assert.ok(opts.includes('coding'), 'use-case options populated: ' + opts.join(','));
  change(window, '#fuse', 'coding');
  await waitFor(() => cardCount(window) > 0);
  dom.window.close();
});

test('freshness line shows crawl age from MODELS_META', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  assert.ok(window.MODELS_META && window.MODELS_META.crawled_at, 'meta present');
  assert.ok(window.document.querySelector('#d-updated').textContent.includes('crawled'),
    'footer shows crawl age');
  dom.window.close();
});

test('wizard picks fit the chosen hardware and use case', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  change(window, '#w-hwcat', 'nvidia');
  await waitFor(() => !window.document.querySelector('#w-hwtier').disabled);
  change(window, '#w-hwtier', '12');
  change(window, '#w-use', 'coding');
  click(window, '#w-go');
  await waitFor(() => window.document.querySelectorAll('#w-results .wrow').length > 0);
  const rows = [...window.document.querySelectorAll('#w-results .wrow')];
  assert.ok(rows.length <= 5, 'top 5 picks max');
  rows.forEach(r => {
    const name = r.querySelector('a').textContent;
    const m = window.MODELS_INDEX.find(x => name.startsWith(x.name));
    assert.ok(m, 'pick maps to a model: ' + name);
    assert.ok(m.est_vram_gb + 1.5 <= 12, name + ' fits NVIDIA 12GB');
    assert.ok((m.best_for || []).includes('coding'), name + ' is good for coding');
  });
  dom.window.close();
});

test('wizard explains when input is incomplete', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  click(window, '#w-go');   // no hardware selected yet
  await waitFor(() => window.document.querySelector('#w-results').textContent.length > 0);
  assert.ok(window.document.querySelector('#w-results').textContent.includes('Pick your hardware'),
    'guidance shown when hardware missing');
  dom.window.close();
});

test('side-by-side compare table shows selected models', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  assert.ok(window.document.querySelectorAll('.cmpbox').length >= 2, 'compare checkboxes on cards');
  click(window, '.cmpbox', 0);
  click(window, '.cmpbox', 1);
  assert.equal(window.document.querySelector('#cmp-bar').style.display, 'block');
  click(window, '#cmp-go');
  await waitFor(() => window.document.querySelector('#cmp-panel').style.display === 'block');
  const body = window.document.querySelector('#cmp-table-body');
  const firstRow = body.querySelector('tr');
  assert.equal(firstRow.querySelector('th').textContent, 'Model');
  assert.equal(firstRow.querySelectorAll('td').length, 2, 'two models compared');
  assert.ok(body.querySelectorAll('tr').length >= 5, 'multiple comparison rows');
  dom.window.close();
});

test('MacBook 48GB wizard NEVER picks DeepSeek-V4-Flash GGUF (parity with Python calc)', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  // the GGUF mirror model exists in the dataset
  const ds = window.MODELS_INDEX.find(m => m.id.includes('DeepSeek-V4-Flash-0731-GGUF'));
  assert.ok(ds, 'DeepSeek-V4-Flash GGUF sample present');
  assert.ok(ds.est_vram_gb + 1.5 > 48 - 3.5, 'sample calc: 88.2 + 1.5 > 44.5 usable');
  // no junk use case pollutes the dropdown
  const uses = [...window.document.querySelector('#w-use').options].map(o => o.value);
  assert.ok(!uses.includes('local-inference'), 'no local-inference junk in dropdown');
  // wizard for MacBook 48 with the reasoning use case
  change(window, '#w-hwcat', 'macbook');
  await waitFor(() => !window.document.querySelector('#w-hwtier').disabled);
  change(window, '#w-hwtier', '48');
  change(window, '#w-use', 'reasoning');
  click(window, '#w-go');
  await waitFor(() => window.document.querySelectorAll('#w-results .wrow').length > 0);
  const rows = [...window.document.querySelectorAll('#w-results .wrow')];
  const names = rows.map(r => r.querySelector('a').textContent);
  assert.ok(!names.some(n => n.includes('DeepSeek V4 Flash')), 'DeepSeek V4 Flash must not be picked for 48GB Mac: ' + names.join(' | '));
  rows.forEach(r => {
    const name = r.querySelector('a').textContent;
    const m = window.MODELS_INDEX.find(x => name.startsWith(x.name));
    assert.ok(m && m.est_vram_gb + 1.5 <= 48 - 3.5, name + ' actually fits MacBook 48GB');
  });
  dom.window.close();
});

test('Intel Arc + Snapdragon wizard parity (new sections use the same fit math)', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  // Arc B580 12 GB: 8B-class picks must fit est + 1.5 <= 12
  change(window, '#w-hwcat', 'intel_arc');
  await waitFor(() => !window.document.querySelector('#w-hwtier').disabled);
  change(window, '#w-hwtier', '12');
  click(window, '#w-go');
  await waitFor(() => window.document.querySelectorAll('#w-results .wrow').length > 0);
  [...window.document.querySelectorAll('#w-results .wrow')].forEach(r => {
    const name = r.querySelector('a').textContent;
    const m = window.MODELS_INDEX.find(x => name.startsWith(x.name));
    assert.ok(m && m.est_vram_gb + 1.5 <= 12, name + ' fits Arc 12GB');
  });
  // Snapdragon 64 GB uses unified-memory math: usable 60.5
  change(window, '#w-hwcat', 'snapdragon');
  await waitFor(() => !window.document.querySelector('#w-hwtier').disabled);
  change(window, '#w-hwtier', '64');
  click(window, '#w-go');
  await waitFor(() => window.document.querySelectorAll('#w-results .wrow').length > 0);
  [...window.document.querySelectorAll('#w-results .wrow')].forEach(r => {
    const name = r.querySelector('a').textContent;
    const m = window.MODELS_INDEX.find(x => name.startsWith(x.name));
    assert.ok(m && m.est_vram_gb + 1.5 <= 64 - 3.5, name + ' fits Snapdragon 64GB unified');
  });
  dom.window.close();
});

test('details pane shows "Run locally with" server chips with links (issue #27)', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  click(window, '.card');
  await waitFor(() => window.document.querySelector('#d-detail').style.display !== 'none', 6000);
  const links = [...window.document.querySelectorAll('#d-servers a')];
  assert.ok(links.length >= 4, 'GGUF model lists GGUF servers, got: ' + links.length);
  links.forEach(a => {
    assert.ok(a.href.startsWith('http'), 'chip links out: ' + a.href);
    assert.ok(a.textContent.includes('↗'), 'chip has open marker');
  });
  const names = links.map(a => a.textContent);
  assert.ok(names.some(n => n.includes('llama.cpp')) && names.some(n => n.includes('Ollama')),
    'llama.cpp + Ollama present');
  dom.window.close();
});

test('wizard: no dropdown, no "best server for" claim — each pick lists ALL servers that can run it on the chosen hardware', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  assert.ok(!window.document.querySelector('#w-server'), 'no server dropdown in wizard');
  change(window, '#w-hwcat', 'nvidia');
  await waitFor(() => !window.document.querySelector('#w-hwtier').disabled);
  change(window, '#w-hwtier', '24');
  click(window, '#w-go');
  await waitFor(() => window.document.querySelectorAll('#w-results .wrow').length > 0);
  assert.ok(!window.document.querySelector('#w-srv-summary'), 'no misleading best-server claim');
  [...window.document.querySelectorAll('#w-results .wrow')].forEach(r => {
    const name = r.querySelector('a').textContent;
    const m = window.MODELS_INDEX.find(x => name.startsWith(x.name));
    assert.ok(m && m.est_vram_gb + 1.5 <= 24, name + ' fits NVIDIA 24GB');
    const sug = r.querySelector('.srv-sug');
    assert.ok(sug && sug.textContent.includes('Run with:'), 'row names servers: ' + name);
    const links = [...sug.querySelectorAll('a')];
    assert.ok(links.length >= 2, name + ' lists ALL runnable servers (got ' + links.length + ')');
    links.forEach(a => assert.ok(a.href.startsWith('http'), 'server chip links out: ' + a.href));
    assert.ok(!sug.textContent.includes('MLX'), 'no MLX on NVIDIA');
    assert.ok(!sug.textContent.includes('TensorRT'), 'no TensorRT-LLM for GGUF');
  });
  dom.window.close();
});

test('details pane RECOMMENDS a server per hardware (issue #30): NVIDIA → Ollama/CUDA, switch to Mac → Metal', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  click(window, '.card');
  await waitFor(() => window.document.querySelector('#d-detail').style.display !== 'none', 6000);
  // default category: nvidia -> recommended Ollama with CUDA badge
  const rec = window.document.querySelector('#d-srv-rec').textContent;
  assert.ok(rec.includes('Recommended') && rec.includes('Ollama'), 'recommendation line: ' + rec);
  assert.ok(rec.includes('CUDA'), 'CUDA badge on NVIDIA: ' + rec);
  const chips = [...window.document.querySelectorAll('#d-servers a')];
  assert.ok(chips.some(c => c.textContent.includes('MLX')) === false, 'no MLX on NVIDIA');
  assert.ok(chips.some(c => c.textContent.includes('vLLM')), 'vLLM listed as experimental alt on NVIDIA');
  // switch category to macbook -> Metal + MLX appears (safetensors-only, so NOT for GGUF model)
  change(window, '#d-srvcat', 'macbook');
  const rec2 = window.document.querySelector('#d-srv-rec').textContent;
  assert.ok(rec2.includes('Metal'), 'Metal badge on Mac: ' + rec2);
  assert.ok(rec2.includes('Ollama'), 'Ollama recommended on Mac for GGUF model');
  assert.ok(![...window.document.querySelectorAll('#d-servers a')].some(c => c.textContent.includes('CUDA')),
    'no CUDA chips on Mac');
  dom.window.close();
});

test('wizard picks show a suggested server per row (issue #30)', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  change(window, '#w-hwcat', 'nvidia');
  await waitFor(() => !window.document.querySelector('#w-hwtier').disabled);
  change(window, '#w-hwtier', '24');
  click(window, '#w-go');
  await waitFor(() => window.document.querySelectorAll('#w-results .wrow').length > 0);
  const rows = [...window.document.querySelectorAll('#w-results .wrow')];
  rows.forEach(r => {
    const sug = r.querySelector('.srv-sug');
    assert.ok(sug && sug.textContent.includes('Run with'), 'row has server suggestion: ' + r.textContent.slice(0,60));
    assert.ok(sug.textContent.includes('badge') || sug.querySelector('.badge'), 'suggestion has backend badge');
  });
  dom.window.close();
});

test('Bootstrap theme: vendored stylesheet linked + wizard shows best-server summary (issue #31 UI)', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  const link = [...window.document.querySelectorAll('link[rel="stylesheet"]')]
    .find(l => (l.href || '').includes('bootstrap.min.css'));
  assert.ok(link, 'bootstrap.min.css linked');
  assert.ok(link.href.startsWith(window.location.href.split('index.html')[0]) || link.href.includes('vendor/'),
    'vendored (local) stylesheet: ' + link.href);
  // card grid uses bootstrap row/col classes
  assert.ok(window.document.querySelector('#list.row'), '#list is a bootstrap row');
  assert.ok(window.document.querySelector('.card.h-100'), 'cards carry bootstrap classes');
  // wizard summary line
  change(window, '#w-hwcat', 'nvidia');
  await waitFor(() => !window.document.querySelector('#w-hwtier').disabled);
  change(window, '#w-hwtier', '24');
  click(window, '#w-go');
  await waitFor(() => window.document.querySelectorAll('#w-results .wrow').length > 0);
  const sum = window.document.querySelector('#w-srv-summary');
  assert.ok(!sum, 'no best-server claim in wizard');
  const styles = [...window.document.querySelectorAll('style')].map(st => st.textContent).join('');
  assert.ok(styles.includes('.pcols') && styles.includes('.cmptable'), 'Quartz overrides in style block');
  dom.window.close();
});

test('Mac Mini + Mac Pro sections appear in hardware filter and wizard (issue: more Macs)', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  const hwOpts = [...window.document.querySelectorAll('#hwcat option')].map(o => o.value);
  assert.ok(hwOpts.includes('mac_mini') && hwOpts.includes('mac_pro'), 'hw filter has Mac Mini/Pro');
  const wOpts = [...window.document.querySelectorAll('#w-hwcat option')].map(o => o.value);
  assert.ok(wOpts.includes('mac_mini') && wOpts.includes('mac_pro'), 'wizard has Mac Mini/Pro');
  change(window, '#w-hwcat', 'mac_mini');
  await waitFor(() => !window.document.querySelector('#w-hwtier').disabled);
  change(window, '#w-hwtier', '64');
  click(window, '#w-go');
  await waitFor(() => window.document.querySelectorAll('#w-results .wrow').length > 0);
  [...window.document.querySelectorAll('#w-results .wrow')].forEach(r => {
    const name = r.querySelector('a').textContent;
    const m = window.MODELS_INDEX.find(x => name.startsWith(x.name));
    assert.ok(m && m.est_vram_gb + 1.5 <= 64 - 3.5, name + ' fits Mac Mini 64GB (unified 60.5)');
  });
  dom.window.close();
});

test('agentic-coding filter + badge (coding/reasoning model with 32K+ context)', async () => {
  const dom = await boot();
  const { window } = dom;
  await waitFor(() => cardCount(window) > 0);
  change(window, '#w-hwcat', 'nvidia');
  await waitFor(() => !window.document.querySelector('#w-hwtier').disabled);
  change(window, '#w-hwtier', '24');
  // without the filter: picks exist
  click(window, '#w-go');
  await waitFor(() => window.document.querySelectorAll('#w-results .wrow').length > 0);
  // with the agentic filter: every pick is a coding/reasoning model with 32K+ ctx
  check(window, '#w-agentic', true);
  click(window, '#w-go');
  await waitFor(() => window.document.querySelectorAll('#w-results .wrow').length > 0);
  [...window.document.querySelectorAll('#w-results .wrow')].forEach(r => {
    const name = r.querySelector('a').textContent;
    const m = window.MODELS_INDEX.find(x => name.startsWith(x.name));
    const tags = (m.best_for || []).join(' ').toLowerCase();
    assert.ok(/(agentic|coding|reasoning|code)/.test(tags), name + ' is coding/reasoning');
    assert.ok((m.context_window || 0) >= 32768, name + ' has 32K+ context');
  });
  // details pane shows the agentic badge for a capable model
  click(window, '.card');
  await waitFor(() => window.document.querySelector('#d-detail').style.display !== 'none', 6000);
  const badge = window.document.querySelector('#d-agentic');
  const sel = window.MODELS_INDEX.find(x => x.id === window.document.querySelector('.card.sel')?.dataset?.id);
  if (sel && agenticTest(sel)) {
    assert.ok(badge && badge.style.display !== 'none' && badge.textContent.includes('Agentic coding ready'),
      'agentic badge visible: ' + (badge && badge.textContent.slice(0,60)));
  }
  dom.window.close();
});

function agenticTest(m){
  const tags = (m.best_for || []).join(' ').toLowerCase();
  return /(agentic|coding|reasoning|code)/.test(tags) && (m.context_window || 0) >= 32768;
}
