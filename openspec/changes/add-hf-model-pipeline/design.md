# Design — Add HF Model Pipeline

## Architecture

```
huggingface.co API  ──►  crawl_models.py  ──►  models/<id>.json  (per-model, schema-valid)
                          │  estimator.py           models/index.json  (summary list)
                          │  artifacts.py           models/index.js   (window.MODELS_INDEX, file://-safe)
                          └  data/state.json        models/bundle.js  (window.MODELS_BUNDLE, file://-safe)
                                                     │
index.html (vanilla) ◄── fetch / script-tag ◄────────┘
```

- `crawl_models.py` — CLI crawler. `GET /api/models?sort=trendingScore&limit=N` with
  repeated `expand=config&expand=safetensors&expand=gguf`, Link-cursor pagination,
  `--limit` (default 150), `--filter` focus (text-generation / gguf). Rate limiting
  (>=0.6s between calls; honor retry-after on 429; HF quota is 500 req / 300 s).
  Resume/checkpoint in `data/state.json`.
- `estimator.py` — pure math, shared by crawler and sample generator:
  - bytes/param: Q4_K_M 0.612, Q5_K_M 0.713, Q8_0 1.063, FP16 2.0 (llama.cpp measured).
  - `size_gb = params_b * bytes/param` (MoE uses TOTAL params — all experts resident).
  - `estimated_vram_gb = size_gb + 1.3` (KV-cache allowance; contract example 4.9 → 6.2).
  - fit(tier) iff `est + 1.5 <= tier` (contract headroom rule, applied exactly once).
  - MacBook usable = `unified - 3.5`; mobile practical iff `params_b <= 4.0` and the
    smallest quant fits an 8 GB budget.
  - GGUF repos: real file sizes from the tree endpoint; else synthesize quants.
- `artifacts.py` — writes per-model JSON (sanitized id: `/` → `__`), `index.json`,
  `index.js`, `bundle.js`. Embedded JS uses `json.dumps(ensure_ascii=False).replace('</','<\\/')`
  so model names can never break the page. Also holds schema load/validate helpers.
- `index.html` — single file, no frameworks. Cards from `models/index.js` (script tag,
  works on file://); details lazy-fetched over http, or from injected `bundle.js` on
  file://; hash deep-links (`#m/<id>`); 150 ms debounced search; chunked rAF rendering;
  hardware boxes recomputed live from the SELECTED quant (stored `hardware{}` = view at
  recommended quant `quants[0]`; invariant: recompute(quants[0]) === hardware{}).
- Containerization — nerdctl (rootless 2.1.2). Dockerfile installs deps in-image
  (python:3.12-slim + ca-certificates + pip requirements), non-root `appuser` uid 1000,
  `ENTRYPOINT ["python","crawl_models.py"]`, `CMD ["--help"]`. Makefile:
  `make build|crawl|serve|clean`, always `--network host` (rootless default bridge is
  hard-coded 10.4.0.0/24 and collides — avoided entirely), run-time
  `--user $(id -u):$(id -g)` so output files are host-owned, `-v` bind mounts for
  `models/` and `data/`. `make serve` overrides the entrypoint:
  `--entrypoint python -m http.server 8000 --directory /app/models`.

## Key decisions

1. **Frontend-first**: hand-written samples (3B → 671B, dense + MoE + GGUF) before any
   crawler code, so the UI contract is proven against real shapes first.
2. **One JSON file per model** in `models/` (user requirement) + index artifacts;
   `models/` is committed as a data snapshot, `data/` is gitignored runtime state.
3. **Fit rule applied exactly once** (worker B caveat): the 1.3 GB KV allowance lives
   inside `estimated_vram_gb`; the +1.5 GB headroom is the fit-test margin. Never both
   at fit time.
4. **file:// support via script tags**, not fetch: `index.js` for cards, `bundle.js`
   for details; hash routing only (pushState throws on file://).
5. **`--network host` + `--user` at run time**: dodges the rootless bridge collision and
   avoids baking a host uid into the image.

## Verification strategy

- `openspec validate add-hf-model-pipeline` (spec gates).
- `pytest -q` hermetic suite (mocked HTTP): schema, extraction, quants, VRAM, flags, resume.
- Sample dataset: schema-valid + `recompute(quants[0]) == hardware{}` invariant +
  `node --check` on emitted JS.
- E2E: real crawler run (--limit 10) → schema-valid `models/` + browser checks
  (search, quant switch flips boxes, extreme MoE = no consumer support, file:// open).
- Nerdctl path: `make -n` dry-runs + README docs. Sandbox cannot execute nerdctl
  (Debian container, root, CapEff=0xcb: no CAP_NET_ADMIN/CAP_SYS_ADMIN — nested
  containerization impossible); host runs `make build`/`make crawl`/`make serve`.
