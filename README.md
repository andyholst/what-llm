# what-llm

What LLM can my hardware actually run?

Two parts, one JSON contract:

1. **Python data pipeline** (`src/whatllm/crawl_models.py`) — fetches currently trending
   models from Hugging Face, extracts metadata (parameters, dense/MoE, GGUF quants,
   downloads), estimates VRAM per quant, and writes **one strict-contract JSON file per
   model** into `models/` (plus `index.json` / `index.js` / `bundle.js`).
2. **Single-file vanilla frontend** (`index.html`) — search by model **or by your
   hardware**: pick a category (NVIDIA / AMD / MacBook / Mac Studio / DGX / Android /
   iPhone) and your VRAM/RAM, tick "only models that fit", and browse models that match.
   Hardware boxes turn green/grey live from the selected quant
   (`est. VRAM + 1.5 GB ≤ device`; Macs use `unified − 3.5 GB`).

## Live demo (GitHub Pages)

The site is auto-deployed to **https://andyholst.github.io/what-llm/** on every merge
to `main` (see `.github/workflows/pages.yml`). The deployment carries
`deploy_info.json` with the live commit sha + timestamp.

Enablement (one-time, repo admin): **Settings → Pages → Source: GitHub Actions → Save**.
After that, every PR merge re-deploys automatically; `workflow_dispatch` re-runs it manually.

## Features

- **Trending HF crawl** — paginated trending feed, GGUF real quant sizes, checkpoint/resume
- **Python-derived model profiles** — what each model is good for: best-for use cases,
  strengths, weaknesses, limitations — every claim with provenance (README-mined,
  benchmark-inferred, or curated)
- **Metadata you can filter on** — license + commercial-friendly gate, context window,
  model type (base/instruct/chat/reasoner/vision), languages, knowledge cutoff,
  best-effort benchmarks (honest verified/unverified)
- **Hardware-fit boxes** — NVIDIA (8–96 GB incl. RTX 5090 32 GB), AMD (8–192 GB
  incl. RX 7900 XT 20 GB), Intel Arc (SYCL/Vulkan), Snapdragon X (unified memory),
  MacBook / Mac Studio (Metal), DGX, Android, iPhone — recomputed live from the
  selected quant (est VRAM + 1.5 GB headroom vs tier), with backend labels
  (CUDA / ROCm / Metal / SYCL+Vulkan) on every section
- **Run locally with → recommended server** — for every (model × hardware) pair the
  site *suggests* the best inference server (Ollama = easiest, LM Studio = GUI,
  MLX = Apple-native, vLLM = throughput, TensorRT-LLM = max NVIDIA) with reasons and
  backend badges; 14-server catalog incl. llama-server, Jan, oobabooga, llamafile,
  gpt4all, SGLang; wizard filters by server and suggests one per pick
- **Search & filters** — name/author/use-case search, hardware-fit mode, type/use-case/
  commercial filters, crawl freshness in the footer
- **Bootstrap 5.3 theme** — vendored `vendor/bootstrap.min.css` (no CDN, no build step); single-file app works over http(s) and file://

## Quickstart

### Full gate (tests) — what CI runs

```sh
make ci          # docker compose: builds + runs the py (pytest) and node (jsdom +
                 # Playwright + node --check + openspec validate) containers
make py-test     # python tests only
make node-test   # node-side checks only
```

GitHub Actions runs `make ci` on every PR and push to `main` — the same command works
locally, so CI and your machine run the identical gate. Requires docker (or rootless
nerdctl aliased as `docker`). On a rootless-nerdctl host, `docker compose run` hardcodes
`-it` (needs a TTY or `script -qec "…" /dev/null`) and may hit the 10.4.0.0/24
default-bridge collision — see AGENTS.md for the fix (restart rootless containerd or
pre-create the network).

### Crawl + serve (nerdctl, host-side)

```sh
make build            # nerdctl build the crawler image
make crawl LIMIT=150  # run the crawler; per-model JSON lands in ./models (bind-mounted)
make serve            # http://localhost:8000 — serves the frontend (index.html + models/)
```

The crawler runs inside the container with `--network host`, `--user $(id -u):$(id -g)`,
and bind mounts for `models/` (output) and `data/` (checkpoint/resume state + HF cache).

## JSON contract (strict — `schemas/model.schema.json`)

Each `models/<author>__<model>.json` file (id with `/` → `__`):

```json
{
  "id": "author/model-name",
  "name": "Display Name",
  "author": "author",
  "parameters_b": 8.19,
  "architecture": "dense | moe",
  "pipeline_tag": "text-generation",
  "hf_url": "https://huggingface.co/author/model-name",
  "trending_score": 1234,
  "downloads": 50000,
  "quants": [{"name": "Q4_K_M", "size_gb": 4.9, "estimated_vram_gb": 6.2, "notes": "…"}],
  "hardware": {
    "nvidia":   {"8gb": false, "12gb": true, "16gb": true, "24gb": true, "48gb": true},
    "amd":      {"8gb": false, "12gb": true, "16gb": true, "24gb": true},
    "macbook":  {"16gb": false, "24gb": true, "32gb": true, "48gb": true, "64gb": true, "96gb": true, "128gb": true},
    "mac_studio":{"32gb": true, "64gb": true, "96gb": true, "128gb": true, "192gb": true, "256gb": true, "512gb": true},
    "dgx":      {"640gb": true, "1128gb": true, "1440gb": true},
    "android":  {"8gb": true, "12gb": true, "16gb": true, "24gb": true, "note": "…"},
    "iphone":   {"8gb": true, "12gb": true, "note": "…"}
  },
  "last_updated": "2026-08-09"
}
```

Rules (contract): `estimated_vram_gb = size_gb + 1.3`; a tier fits iff
`est + 1.5 ≤ tier_vram`; MacBook/Mac Studio use `unified − 3.5`; DGX uses total system
GPU memory (DGX A100/H100 640, H200 1128, B200 1440 GB); phones are practical only for
≤4 B models whose smallest quant fits an 8 GB budget. MoE uses TOTAL parameters (all
experts resident). Bytes/param: Q4_K_M 0.612, Q5_K_M 0.713, Q8_0 1.063, FP16 2.0
(llama.cpp measured); GGUF repos use real file sizes from the HF tree endpoint.

## Layout

```
src/whatllm/            Python package (estimator, artifacts, crawler, make_samples)
schemas/                model.schema.json (strict contract)
models/                 generated per-model JSON + index artifacts (committed snapshot)
data/                   gitignored runtime state (checkpoint, logs, HF cache)
index.html              single-file vanilla frontend
tests/                  pytest (python) + frontend.test.mjs (jsdom) + e2e/ (Playwright)
docker-compose-files/   CI compose (py + node services)
docker/                 py.Dockerfile, node.Dockerfile
openspec/               spec-driven changes (add-hf-model-pipeline, expand-hardware-tiers, add-compose-ci-harness)
```

## License

Apache License 2.0 — see [LICENSE](LICENSE). See [AGENTS.md](AGENTS.md) for the
behavior contract (test parity, CI gate, OpenSpec discipline).
