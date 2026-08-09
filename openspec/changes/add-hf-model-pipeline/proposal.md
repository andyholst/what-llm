# Add HF Model Pipeline

## Why

what-llm needs a repeatable, truthful source of "can I run this model on my hardware?"
data. Today that data is manual. We need a pipeline that fetches trending Hugging Face
models, extracts real metadata (params, architecture, GGUF quants, downloads), computes
per-quant VRAM estimates, maps them onto NVIDIA / AMD / MacBook / mobile hardware tiers,
and renders the result in a dependency-free single-file frontend. The whole build and
run path must go through nerdctl with a Dockerfile (deps set up in-image) and bind-mounted
volumes so generated JSON persists on the host.

## What Changes

- A Python crawler (`crawl_models.py`) hitting the HF API
  (`GET /api/models?sort=trendingScore&limit=N`, Link-cursor pagination, repeated
  `expand=config&expand=safetensors&expand=gguf`) that emits **one validated JSON file per
  model** into `models/` plus `models/index.json`, `models/index.js` and `models/bundle.js`.
- A strict JSON Schema contract (`schemas/model.schema.json`) enforced at write time.
- A single-file `index.html` frontend: search, model cards, quant selector, NVIDIA / AMD /
  MacBook / mobile hardware boxes that turn green/grey from the selected quant's
  `estimated_vram_gb + 1.5` headroom rule; mobile-friendly; works via local server and
  degrades gracefully on `file://` (script-tag index + injected bundle).
- Containerized execution: Dockerfile + Makefile driving **nerdctl** build/run with
  `--network host`, run-time `--user $(id -u):$(id -g)`, and `-v` volume mounts for
  `models/` and `data/`.
- Repository licensed under **Apache License 2.0** (`LICENSE`).

## Capabilities

### New Capabilities

- `model-pipeline`: crawling HF trending models (--limit, rate limiting, resume/checkpoint),
  dense-vs-MoE detection, GGUF quant discovery, per-quant VRAM estimation
  (`size_gb + 1.3`; fit iff `est + 1.5 <= tier`, MacBook `unified - 3.5`, mobile <= 4B),
  hardware flag mapping anchored on the recommended quant, schema-validated per-model
  output files, and a vanilla frontend that recomputes boxes live from the selected quant.

## Impact

- `models/` is a committed artifact snapshot (regenerate with `make crawl`); `data/` is
  gitignored runtime state (checkpoint, logs, HF cache).
- Frontend works with hand-written sample data first, then real crawler output.
- All commands run through `make` → nerdctl; no host Python/deps required.
- GitHub remote: `andyholst/what-llm` (public), Apache-2.0 licensed.
