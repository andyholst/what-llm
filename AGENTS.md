# AGENTS.md — what-llm

Behavior contract for AI agents working in this repository. Live document: append
lessons and gaps as they are discovered.

## Project shape

- **Two parts**: a Python crawler (`crawl_models.py`) that fetches trending Hugging Face
  models and emits **one strict-contract JSON file per model** into `models/`, plus
  `index.json` / `index.js` / `bundle.js`; and a single-file vanilla frontend
  (`index.html`) that renders cards, a quant selector, and NVIDIA / AMD / MacBook /
  mobile hardware boxes that flip green/grey live.
- **OpenSpec-driven**: all work is tracked in `openspec/changes/add-hf-model-pipeline/`
  (proposal / design / specs / tasks). Every step of a build MUST be an OpenSpec task;
  tick a box `- [x]` ONLY after the task is verified with real output. Never hand-author
  a change directory — create via `openspec new change <name>` (CLI). Keep
  `openspec validate add-hf-model-pipeline` green. Update this file when a durable rule
  or gap is learned.

## Hard rules (learned, do not regress)

- **JSON contract** is enforced by `schemas/model.schema.json` (additionalProperties:
  false). `estimated_vram_gb = size_gb + 1.3` (KV allowance); fit iff
  `est + 1.5 <= tier` — the headroom is applied exactly once, never double-counted.
  MoE uses TOTAL parameters (all experts resident). MacBook usable = unified − 3.5.
  Mobile practical iff params_b ≤ 4.0 and smallest quant fits an 8 GB budget.
- **HF API**: use repeated `expand=config&expand=safetensors&expand=gguf` (the
  `expand[]=` bracket form also parses, but the plain repeated form is the documented
  safe one; `expand=blobs` is INVALID). Params come from `safetensors.total`.
  Paginate via the `Link` header cursor (opaque base64); list caps at 1000. GGUF repos
  are detected by `'gguf' in tags` (library_name is often None). Quota ~500 req/300s.
- **Per-model filenames**: `author__model.json` (`/` → `__`). JS artifacts MUST escape
  `</` → `<\/` (json.dumps(...).replace('</','<\\/')) so model names can't break
  `<script>` blocks.
- **nerdctl (rootless 2.1.2)**: every run command goes through nerdctl + Dockerfile with
  bind mounts. Use `--network host` (default bridge is hard-coded 10.4.0.0/24 and
  collides; compose ipam/name/external overrides are ignored). Never add
  `default_subnet` to `~/.config/nerdctl/nerdctl.toml` (strict mode blocks everything).
  `docker compose run` under nerdctl hardcodes `-it` → wrap in `script -qec "…" /dev/null`.
  Run as the host user: `--user $(id -u):$(id -g)`.
- **Sandbox limitation (this dev container)**: root, CapEff=0xcb → no CAP_NET_ADMIN /
  CAP_SYS_ADMIN → nerdctl/containerd CANNOT run here (nested containerization
  impossible). Verify the pipeline in the container-equivalent venv
  (`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`), validate
  nerdctl targets with `make -n` dry-runs, and document the host path in the README.
  NEVER claim a nerdctl build/run succeeded when it did not execute.
- **Git/GitHub**: repo `andyholst/what-llm` (public, Apache-2.0). Identity: Asimov Agent
  <support@docondee.com>. Token lives in gitignored `.env` (`GH_TOKEN`); never commit it
  and never print it. Push with the credential-helper pattern (`username=x-access-token`,
  `password=$GH_TOKEN`) — git-over-HTTPS needs Basic auth, Bearer only works for the REST
  API. No squash/rebase/force-push of pushed history.
- **Secrets**: `.env` is gitignored; do not paste tokens into issues/PRs/commits.
- **models/ is committed** (data snapshot; regenerate with `make crawl`). `data/` is
  gitignored runtime state (checkpoint, logs, HF cache).
- **Python layout**: all Python lives in `src/whatllm/` (package, `pip install -e .`);
  the root keeps only config/docs/data directories — no loose .py files.

## Harness behavior (CI + iterative PRs)

- **Small topo tasks**: tasks.md contains small, topologically-ordered units; a task is
  done only when verified locally AND by the GitHub Actions CI pipeline on its PR.
- **TEST PARITY (no exceptions)**: every code change or new requirement MUST ship with
  new tests — Python changes get pytest cases; HTML/JS changes (index.html included) get
  jsdom unit tests AND Playwright browser specs. The frontend's JS is tested with dev
  npm dependencies (jsdom, @playwright/test) as part of the CI node container. A PR that
  changes code without adding/changing tests fails the gate.
- **Iterative delivery**: completed task groups ship as small PRs (feat/<milestone> →
  main). Every PR must be CI-green before merge; never merge with failing checks.
- **CI pipeline**: `.github/workflows/ci.yml` runs `make ci` (docker compose: py +
  node containers — pytest, jsdom, Playwright, node --check, openspec validate).
  Tests MUST stay hermetic (mocked HTTP) — CI has no HF access.
- **OpenSpec validity is part of the gate**: every active change MUST pass
  `openspec validate` (run inside the node container in CI). NEVER commit or push
  invalid OpenSpec files — validate before any commit/PR.
- **Ticking boxes**: tick `- [x]` only after the verification actually passed (locally
  and in the PR's CI run); never tick ahead of verification.
- **Merges**: regular merge (no squash/rebase/force-push of pushed history).

## Discovered gaps / fixes (append as found)

- 2026-08-09: `expand[]=` vs repeated `expand=` — both parse; use repeated form.
- 2026-08-09: model ids contain `/` → sanitize to `__` for filenames; frontend derives
  filename as `id.replace('/','__') + '.json'`.
- 2026-08-09: `fetch()` is CORS-blocked on `file://` → script-tag `index.js` for cards +
  injected `bundle.js` for details; hash deep-links only (`pushState` throws on file://).
- 2026-08-09: rootless nerdctl default bridge collision → `--network host` everywhere.
- 2026-08-09: sandbox cannot run nerdctl (no CAP_NET_ADMIN) → `make -n` + venv E2E.
- 2026-08-09 (skeptic-verified): `expand[]=` and repeated `expand=` BOTH work — the only
  real bug was the invalid VALUE `blobs`. Use whitelisted values only.
- 2026-08-09 (skeptic-verified): `expand=gguf`'s `total` is the PARAMETER COUNT, not
  bytes; `totalFileSize` is unreliable (ratios 4.0/0.61/2.0 measured) — use the tree
  endpoint for real file sizes.
- 2026-08-09 (skeptic-verified): MoE detection MUST use config.model_type /
  num_experts — `DeepseekV3ForCausalLM` contains no 'Moe'; arch substring alone is
  neither necessary nor sufficient.
- 2026-08-09 (skeptic-verified): Mixtral 46.7B Q4_K_M: with the CONTRACT formula
  (est = size + 1.3, fit = est + 1.5 <= tier) est is 29.88, so 32 GB MacBook (usable
  28.5) does NOT fit (31.38 > 28.5) — only 48 GB+ tiers fit. Keep 2-decimal math for
  tier boundaries.
- 2026-08-09 (skeptic): MacBook −3.5 GB and mobile ≤4 B are heuristics, not measured
  facts — labeled as such in the docs.
- 2026-08-09 (crawler): quant tokens are underscore-prefixed (`Q4_K_M` = Q4+_K+_M) and
  split GGUF files end `-00001-of-00002.gguf` — quant regex must allow both.
- 2026-08-09 (crawler): DeepSeek-V3 has NO 'moe' in model_type/architectures — MoE
  detection must also check expert config keys (n_routed_experts, num_experts, ...).
- 2026-08-09 (live E2E): the LIST endpoint DROPS pipeline_tag/tags when expand= is
  passed — fetch the list PLAIN (for filtering) and details per-model with
  expand=config&expand=safetensors&expand=gguf&expand=tags.
- 2026-08-09 (CI): the py test container needs `make` installed — tests/test_makefile.py
  runs `make -n` inside pytest.
- 2026-08-09 (decision): models/ is committed as the deterministic SAMPLE dataset —
  tests couple to it (searches like "DeepSeek-R1"). The real crawl output is verified
  live (`python -m whatllm.crawl_models --out /tmp/...`) and regenerated on the host
  with `make crawl`; never overwrite models/ with real data and commit it blindly.

## Verification gate (before ticking any task)

1. `openspec validate add-hf-model-pipeline` → valid.
2. `pytest -q` green (hermetic, mocked HTTP).
3. Emitted artifacts: every `models/*.json` passes the schema; invariant
   `recompute(quants[0]) == hardware{}`; `node --check` on `index.js`/`bundle.js`.
4. Frontend E2E: served page + `file://` open both work; quant switch flips boxes;
   extreme MoE shows no consumer support.
5. `make -n` dry-run clean for build/crawl/serve/clean.
