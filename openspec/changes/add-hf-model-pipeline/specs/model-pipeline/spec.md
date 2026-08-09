## ADDED Requirements

### Requirement: Strict model JSON contract
Every crawler output file MUST conform to `schemas/model.schema.json` with fields: id, name, author, parameters_b, architecture (dense|moe), pipeline_tag, hf_url, trending_score, downloads, quants[{name,size_gb,estimated_vram_gb,notes}], hardware{nvidia,amd,macbook,mobile}, last_updated, and MUST NOT contain extra fields.

#### Scenario: Schema-valid output
- **WHEN** the crawler emits a per-model file
- **THEN** the file is validated against the schema and invalid records are skipped with a logged error

#### Scenario: Sample data conformance
- **WHEN** hand-written sample models are added before the frontend exists
- **THEN** every sample passes schema validation so the frontend renders real contract shapes

### Requirement: Per-model output files
The crawler MUST write one JSON file per model into `models/` (sanitized id, `/` replaced by `__`) and MUST regenerate `models/index.json` plus `models/index.js` and `models/bundle.js` after every run so the frontend can render cards and details.

#### Scenario: Index consistency
- **WHEN** a crawl run completes
- **THEN** every file in `models/` is schema-valid, index.json lists all model ids, and index.js/bundle.js pass a JS syntax check

### Requirement: Trending model discovery with pagination
The crawler SHALL fetch Hugging Face trending models via `GET /api/models?sort=trendingScore&limit=N` with repeated `expand=config&expand=safetensors&expand=gguf`, SHALL paginate via the Link cursor header until exhausted or `--limit` is reached, and SHALL respect a rate-limit delay between requests.

#### Scenario: Limited run
- **WHEN** the crawler runs with `--limit 5`
- **THEN** it stops after 5 models and logs the pages fetched

### Requirement: Metadata and architecture extraction
The crawler MUST extract `parameters_b` from the safetensors total parameter count and MUST classify each model as dense or moe from its architectures / model_type / expert keys in the config.

#### Scenario: MoE model
- **WHEN** a model's config contains MoE markers (e.g. *Moe* architecture, model_type containing "moe", or num_experts)
- **THEN** architecture is `moe` and parameters_b reflects the total (all-expert) parameter count

### Requirement: GGUF quant discovery and VRAM estimation
The crawler MUST discover GGUF quant files (name, size_gb) from repos tagged gguf (tree endpoint file sizes) and SHALL compute `estimated_vram_gb = round(size_gb + 1.3, 2)` for each quant; for models without GGUF files it SHALL synthesize quants from the bytes-per-parameter table (Q4_K_M 0.612, Q5_K_M 0.713, Q8_0 1.063, FP16 2.0) using total parameters.

#### Scenario: Quant list built
- **WHEN** a repo contains multiple `.gguf` files
- **THEN** each recognized quant yields an entry with size and estimated VRAM, and non-GGUF files are skipped

### Requirement: Hardware flag mapping
Each model's hardware flags (nvidia, amd, macbook, mobile) MUST be derived from the recommended quant (quants[0]): a tier is enabled iff `estimated_vram_gb + 1.5 <= tier_vram`, MacBook compares against `unified_memory - 3.5`, and mobile is practical only for models with parameters_b <= 4.0 whose smallest quant fits an 8 GB budget.

#### Scenario: Headroom rule
- **WHEN** a quant needs 6.2 GB estimated VRAM
- **THEN** boxes for tiers with 8 GB or more go green (6.2 + 1.5 = 7.7 <= 8) and all smaller tiers stay grey

#### Scenario: Extreme MoE
- **WHEN** a MoE model's quant estimate exceeds every consumer tier (e.g. 400+ GB)
- **THEN** all consumer hardware flags are false and the mobile note explains there is no consumer support

### Requirement: Resilient crawling
The crawler MUST implement rate limiting (polite delay, honor retry-after on 429) and SHALL persist a checkpoint in `data/state.json` so an interrupted run resumes without re-fetching completed models.

#### Scenario: Resume after interruption
- **WHEN** a run is interrupted and re-invoked
- **THEN** already-fetched models are skipped and only remaining pages are crawled

### Requirement: Single-file frontend with live hardware boxes
The frontend MUST be a single `index.html` with vanilla HTML/CSS/JS: search, model cards, quant selector, and NVIDIA/AMD/MacBook/mobile hardware boxes that update live from the selected quant, SHALL work on mobile, and SHALL degrade gracefully when opened via `file://` (script-tag index, injected bundle, friendly error instead of a blank screen).

#### Scenario: file:// open
- **WHEN** `index.html` is opened directly from disk and fetch of `models/<id>.json` is unavailable
- **THEN** the page renders cards from models/index.js and model details from models/bundle.js instead of a blank screen

#### Scenario: Quant switch recomputes boxes
- **WHEN** the user selects a different quant for a model
- **THEN** every hardware box is recomputed from that quant's estimated_vram_gb and flips green/grey accordingly

### Requirement: Containerized execution via nerdctl
All run commands SHALL go through nerdctl with a Dockerfile that installs dependencies in-image, and the container MUST mount `models/` and `data/` as bind volumes so generated JSON and checkpoint state persist on the host; networking SHALL use `--network host` to avoid the rootless default bridge, and the process SHALL run as the invoking host user via `--user $(id -u):$(id -g)`.

#### Scenario: Volume-mounted crawl
- **WHEN** `make crawl LIMIT=5` runs inside the container
- **THEN** validated per-model files and index appear in the host-mounted `models/` directory

### Requirement: Apache-2.0 licensing
The repository MUST ship an Apache License 2.0 LICENSE file at the repository root.

#### Scenario: License present
- **WHEN** the repository is cloned
- **THEN** a LICENSE file containing the Apache License 2.0 text exists at the root

### Requirement: CI-verified iterative delivery
Every PR SHALL run the GitHub Actions CI pipeline (pytest suite, node --test frontend suite, node --check on emitted JS, make -n dry-runs, openspec validate) and SHALL NOT be merged while any check fails; tasks are implemented in small topologically-ordered units and delivered as small iterative PRs.

#### Scenario: PR gate
- **WHEN** a PR branch is pushed for a completed task group
- **THEN** the CI pipeline runs all checks and the PR is merged only after every check passes

#### Scenario: Task verification
- **WHEN** a task's verification passes locally and in the CI pipeline for its PR
- **THEN** the corresponding tasks.md box is ticked `- [x]`

## ADDED Acceptance Criteria

- `openspec validate add-hf-model-pipeline` reports valid.
- GitHub Actions CI runs on every PR (pytest, npm test, node --check, make -n, openspec validate) and is green before merge.
- `pytest -q` (hermetic, mocked HTTP) passes in the container-equivalent environment and in CI.
- A real crawler run produces schema-valid `models/<id>.json` per model plus index artifacts, with the invariant recompute(quants[0]) == hardware{} for every model.
- Frontend loads from both a local server and `file://`; search, quant selector, and hardware boxes work and update live from crawler output; extreme MoE models show no consumer support.
- `make -n` dry-runs cleanly for build/crawl/serve/clean; the host nerdctl path is documented in README (sandbox cannot execute nerdctl: no CAP_NET_ADMIN, nested containerization impossible).
- Every box in tasks.md is `- [x]` after verification; repo committed and pushed to andyholst/what-llm.
