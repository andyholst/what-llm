# Tasks — add-hf-model-pipeline

Delivery model: every task is SMALL and topologically ordered (later tasks depend on
earlier ones). Tasks ship as small iterative PRs; each PR must pass the GitHub Actions
CI pipeline (pytest + node tests + node --check + make -n + openspec validate) BEFORE it
is merged. A box is ticked `- [x]` only after its verification passed — locally first,
then in the CI pipeline for its PR.

## 1. Scaffolding — ships as PR-1

- [x] 1.1 Add `.gitignore` (data/, .venv/, node_modules/, __pycache__/, *.pyc, .env, .DS_Store); models/ stays TRACKED
  - [x] Verify: `git check-ignore .env data/` exits 0; models/ not ignored
- [x] 1.2 Add `LICENSE` (Apache License 2.0, canonical text)
  - [x] Verify: first line contains "Apache License"; file tracked
- [x] 1.3 Add `requirements.txt` (huggingface_hub, requests, jsonschema)
  - [x] Verify: `pip install -r requirements.txt` resolves in a clean venv
- [x] 1.4 Add `README.md` stub (purpose, status, license)
  - [x] Verify: renders; no placeholder TODOs left
- [x] 1.5 OpenSpec: install @fission-ai/openspec (--no-save), `openspec init`, scaffold change dir via `openspec new change add-hf-model-pipeline` (CLI only)
  - [x] Verify: `openspec list` shows the change; `openspec validate add-hf-model-pipeline` is valid
- [x] 1.6 Add `package.json` (jsdom devDependency; `npm test` -> node --test)
  - [x] Verify: `npm install` resolves; `npm test` runs the (smoke) suite
- [x] 1.7 Add CI pipeline `.github/workflows/ci.yml` (ubuntu, python 3.12, node 20: pip install, pytest, npm test, node --check on models/*.js if present, make -n build/crawl/serve/clean, openspec validate)
  - [x] Verify: workflow file YAML-valid; a local run of each step succeeds in the venv
- [x] 1.8 Add `tests/test_smoke.py` (imports, schema path exists, estimator imports)
  - [x] Verify: `pytest tests/test_smoke.py -q` green locally
- [x] 1.9 Commit scaffold, push branch, open PR-1, wait for CI green, merge
  - [x] Verify: GitHub Actions run on PR-1 shows all checks passing; PR merged

## 2. Contract & estimator — ships as PR-2

- [x] 2.1 Add `schemas/model.schema.json` (strict contract, additionalProperties false, enums, hardware flags)
  - [x] Verify: good record validates; bad records fail (pytest)
- [x] 2.2 Add `tests/test_schema.py` (required fields, enum violations, extra fields, quant shape, date pattern)
  - [x] Verify: `pytest tests/test_schema.py -q` green
- [x] 2.3 Add `estimator.py` core: BYTES_PER_PARAM (Q4_K_M 0.612, Q5_K_M 0.713, Q8_0 1.063, FP16 2.0), quant_size_gb, est_vram_gb (size + 1.3), fits (est + 1.5 <= tier)
  - [x] Verify: 8B Q4_K_M -> 4.9 GB size, 6.2 est, fits 8 GB (7.7 <= 8)
- [x] 2.4 Add `estimator.py` hardware flags: nvidia/amd/macbook tiers, MacBook unified - 3.5, mobile practical iff params_b <= 4.0 and min quant fits 8 GB, MoE uses TOTAL params
  - [x] Verify: Mixtral 46.7B Q4_K_M est 29.88 -> 32 GB MacBook does NOT fit (31.38 > 28.5 usable), 48 GB+ tiers fit; extreme MoE all-false + note
- [x] 2.5 Add `tests/test_estimator.py` (formula values, tier boundaries with 2-decimal math, MacBook, mobile, MoE totals, DeepSeek-R1 all false)
  - [x] Verify: `pytest tests/test_estimator.py -q` green
- [x] 2.6 Add package layout: pyproject.toml + src/whatllm package (estimator, artifacts, make_samples); root keeps only config/docs/data dirs, no loose .py
  - [x] Verify: `pip install -e .` works; `python -m whatllm.make_samples` runs; `ls *.py` at root is empty
- [x] 2.7 Commit, push branch, PR-2, CI green, merge
  - [x] Verify: CI passes on PR-2; PR merged

## 3. Artifacts & sample data — ships as PR-3

- [x] 3.1 Add `artifacts.py`: per-model file writer (id `/` -> `__`), index.json, index.js, bundle.js; `</` -> `<\/` escaping in JS
  - [x] Verify: filenames sanitized; emitted JS round-trips through node
- [x] 3.2 Add `tests/test_artifacts.py` (sanitize, escaping round-trip, index/bundle shape, schema validity of written files)
  - [x] Verify: `pytest tests/test_artifacts.py -q` green
- [x] 3.3 Add `make_samples.py` + 8 hand-written samples (3.8B..671B: dense, MoE, GGUF-with-real-sizes, extreme MoE)
  - [x] Verify: `python make_samples.py` emits all files; verify() reports 0 problems
- [x] 3.4 Add samples invariant test: recompute(quants[0]) == hardware{} for every sample; node --check on index.js/bundle.js in CI
  - [x] Verify: invariant holds for all 8 samples; node --check passes
- [x] 3.5 Commit, push branch, PR-3, CI green, merge
  - [x] Verify: CI passes on PR-3; PR merged

## 4. Frontend — ships as PR-4

- [x] 4.1 `index.html` shell: loads models/index.js, search box + model cards (name, author, params, downloads, pipeline_tag)
  - [x] Verify: served page renders all sample cards; search filters (local + jsdom)
- [x] 4.2 Quant chips + hardware boxes (NVIDIA 8/12/16/24/48, AMD 8/12/16/24, MacBook 16/24/32/48+, mobile): green iff est + 1.5 <= tier; live recompute from SELECTED quant, stored hardware{} fallback
  - [x] Verify: switching quants flips boxes per fit rule (jsdom test)
- [x] 4.3 Details pane (facts, hf_url, quant notes) + mobile-responsive layout + hash deep-links (#m/<id>)
  - [x] Verify: details open via hash; no horizontal scroll at 400px
- [x] 4.4 file:// fallback: bundle.js injection on file://, server hint on missing bundle, no pushState
  - [x] Verify: jsdom (file:// semantics) renders details from bundle; fetch path also works served
- [x] 4.5 Add `tests/frontend.test.mjs` (jsdom: boot, search filter, card click, quant switch flips boxes, extreme MoE all grey, escaping safe)
  - [x] Verify: `npm test` green locally
- [x] 4.6 Commit, push branch, PR-4, CI green, merge
  - [x] Verify: CI passes on PR-4; PR merged

## 5. Crawler — ships as PR-5 (topological: 5.1 -> 5.13)

- [x] 5.1 Add HTTP layer in `crawl_models.py`: injectable `get_json`, list endpoint with repeated expand=config&expand=safetensors&expand=gguf, Link-cursor pagination, page cap
  - [x] Verify: mocked pages paginate and stop at cap (pytest)
- [x] 5.2 Add `tests/test_crawler_api.py` (mocked list response, cursor loop, limit enforcement)
  - [x] Verify: green
- [x] 5.3 Add metadata extraction: parameters_b from safetensors.total; dense/MoE via config.model_type + num_experts + architectures (NEVER arch substring alone — DeepseekV3ForCausalLM has no 'Moe'); skip+log models without params
  - [x] Verify: dense, qwen3_moe, deepseek_v3, and no-params cases handled (pytest)
- [x] 5.4 Add `tests/test_crawler_extract.py`
  - [x] Verify: green
- [x] 5.5 Add GGUF discovery: 'gguf' in tags -> tree endpoint per-file sizes; quant regex `-(Q\d+_K|IQ\d|Q\d+_[KMSL]|Q8_0)\.gguf$`; cap 8 quants sorted by size; mirror-search fallback; synthesize fallback via estimator
  - [x] Verify: fixture tree -> expected quants; unknown files skipped; cap honored
- [x] 5.6 Add `tests/test_crawler_gguf.py`
  - [x] Verify: green
- [x] 5.7 Wire VRAM estimation + hardware flags (estimator) + schema validation gate (skip+log invalid before write)
  - [x] Verify: bad record skipped with logged error; good ones pass
- [x] 5.8 Add `tests/test_crawler_validate.py`
  - [x] Verify: green
- [x] 5.9 Add rate limiting (>=0.6s delay; honor retry-after on 429) + resume/checkpoint `data/state.json` (completed models recorded)
  - [x] Verify: interrupted re-run skips completed models (mocked)
- [x] 5.10 Add `tests/test_crawler_resume.py`
  - [x] Verify: green
- [x] 5.11 Add CLI: --limit (default 150), --filter (text-generation/gguf focus), --out, --dry-run, --help
  - [x] Verify: `python crawl_models.py --help` exits 0; --dry-run --limit 3 logs pages
- [x] 5.12 Add `tests/test_crawler_cli.py`
  - [x] Verify: green
- [x] 5.13 Local REAL run: `python crawl_models.py --limit 10` (network) -> schema-valid models/ + index + bundles
  - [x] Verify: all outputs schema-valid; invariant holds; node --check passes
- [x] 5.14 Commit, push branch, PR-5, CI green, merge
  - [x] Verify: CI passes on PR-5; PR merged

## 6. Containerization & docs — ships as PR-6

- [x] 6.1 Add `Dockerfile` (python:3.12-slim, ca-certificates, requirements.txt, non-root appuser uid 1000, ENTRYPOINT python crawl_models.py, CMD --help, HF_HOME=/app/data/hf-cache)
  - [x] Verify: dockerfile syntax valid (hadolint-style review); consistent with Makefile
- [x] 6.2 Add `.dockerignore` (models/, data/, .venv/, node_modules/, openspec/, *.md except README, .git)
  - [x] Verify: `git check-ignore` semantics via dry-run; list covers all dev dirs
- [x] 6.3 Add `Makefile`: build/crawl/serve/clean via nerdctl; --network host; --user $(id -u):$(id -g); -v $(CURDIR)/models:/app/models and data; serve overrides --entrypoint python -m http.server
  - [x] Verify: `make -n build crawl serve clean` all parse (CI)
- [x] 6.4 Add `tests/test_makefile.py` (make -n exit 0; target strings contain --network host, -v mounts, --user, --entrypoint override)
  - [x] Verify: green
- [x] 6.5 Complete `README.md` (make targets, nerdctl host notes, contract summary, frontend usage, license)
  - [x] Verify: README documents every make target and the host nerdctl path
- [x] 6.6 Finalize `AGENTS.md` (harness behavior: CI gate, PR flow, learned gaps)
  - [x] Verify: sections match actual repo state
- [x] 6.7 Commit, push branch, PR-6, CI green, merge
  - [x] Verify: CI passes on PR-6; PR merged

## 7. Final verification & close-out

- [x] 7.1 Browser E2E (local): served page + file:// open; search; quant switch flips boxes; extreme MoE shows no consumer support; mobile layout
  - [x] Verify: real browser DOM checks pass for crawler-generated data
- [x] 7.2 Re-run all gates: openspec validate, full pytest, npm test, node --check, make -n
  - [x] Verify: all green; `openspec status --change` shows 4/4 artifacts
- [ ] 7.3 Tick every box `- [x]` (only those CI/local-verified), commit, push main, report
  - [x] Verify: zero `- [x]` remain; remote main up to date; repo page reachable
