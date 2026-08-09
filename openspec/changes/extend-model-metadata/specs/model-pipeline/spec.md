## ADDED Requirements

### Requirement: Python-derived model profile
Every model file MUST include a `profile` object: `summary`, `best_for[]`, `strengths[]`,
`weaknesses[]`, `limitations[]`, and `provenance[]`. The crawler MUST derive these
programmatically: README section mining (normalized headings for limitations, weaknesses,
strengths, intended use), structured inference (evalResults entries → strength
candidates, context window → capability note, license → limitation, ISO tags →
languages), and a curated family fallback when the README is gated or absent. Every
profile claim MUST carry provenance (source: readme | evals | config | tags | curated,
plus confidence).

#### Scenario: README with limitation section
- **WHEN** a model's README contains a `## Limitations` (or normalized equivalent) section
- **THEN** the bullet points appear in `profile.limitations[]` tagged `source: readme`

#### Scenario: eval results present
- **WHEN** `expand[]=evalResults` returns entries
- **THEN** a strength candidate references the dataset id + value with the `verified`
  flag surfaced verbatim (default `false`), tagged `source: evals`

#### Scenario: gated model
- **WHEN** the API reports `gated != false` for a model
- **THEN** the crawler skips the README fetch entirely and the profile falls back to
  curated family data plus structured signals, and `limitations[]` notes the gated card

### Requirement: License and commercial gate
Every model file MUST include `license` and `commercial_ok`. The crawler MUST read
`cardData.license` (or the `license:*` tag) and compute `commercial_ok` against a
curated non-commercial denylist.

#### Scenario: non-commercial license
- **WHEN** the license is on the non-commercial denylist (e.g. cc-by-nc, llama3.x restricted)
- **THEN** `commercial_ok` is `false` and a limitation entry explains the restriction

### Requirement: Context window
Every model file MUST include `context_window` (nullable). The crawler MUST fetch the
raw `config.json` per model and read `max_position_embeddings`, falling back to
`n_positions` / `sliding_window`. Gated models are skipped without error.

#### Scenario: context from raw config
- **WHEN** a model's raw `config.json` contains `max_position_embeddings: 40960`
- **THEN** `context_window` is `40960` and the profile capability note mentions it

### Requirement: Model-type taxonomy
Every model file MUST include `model_type` (base | instruct | chat | reasoner | vision).
The crawler MUST use `cardData.base_model` (a LIST when present; the top-level
`base_model` key is null on both instruct and base models) plus id-suffix heuristics,
with a curated override table for MoE/coder/reasoner variants.

#### Scenario: instruct model
- **WHEN** `cardData.base_model` lists a base model (e.g. `["Qwen/Qwen3-8B-Base"]`)
- **THEN** `model_type` is `instruct` (unless overridden), and the UI shows a badge

### Requirement: Languages and best-effort knowledge cutoff
Every model file MUST include `languages[]` (ISO codes from tags) and `knowledge_cutoff`
(nullable, README-prose only, never guaranteed).

#### Scenario: language tags
- **WHEN** a model carries ISO language tags
- **THEN** `languages[]` contains them and the profile strength may mention them

### Requirement: Best-effort benchmarks
Every model file MUST include `benchmarks[]` built from `evalResults` (a LIST of
`{filename, verified, data, pullRequest}` entries; 0–2 per model typical). Values are
never presented as authoritative: the `verified` flag defaults to `false`.

#### Scenario: unverified benchmark
- **WHEN** an evalResults entry has `verified: false`
- **THEN** the benchmark is shown with an explicit "unverified" marker

### Requirement: Rate-aware metadata enrichment
The enrichment SHALL stay within the anonymous quota (500 requests per fixed 5-minute
window): list + detail + tree + README + config ≈ 482 requests per 150 models (~96%),
so the crawler MUST keep 0.6 s pacing, skip gated READMEs, and reuse the resume
checkpoint so an interrupted run never restarts a window.

#### Scenario: window pressure
- **WHEN** a run would exceed ~90% of the 5-minute window budget
- **THEN** the crawler pauses and resumes via checkpoint rather than risking 429s

## ADDED Acceptance Criteria

- `profile` exists on every model file with `best_for`, `strengths`, `weaknesses`,
  `limitations`, and `provenance`; each claim has a source tag.
- `license` + `commercial_ok`, `context_window`, `model_type`, `languages[]`,
  `knowledge_cutoff` (nullable), and `benchmarks[]` (with `verified` flags) are present.
- The crawler derives everything programmatically (README mining + structured
  inference + curated fallback); no hand-written profiles in the pipeline output.
- Hermetic tests cover gated/ungated READMEs, eval list shape, base_model LIST nuance,
  and the 96%-of-window budget math.
- `openspec validate extend-model-metadata` is valid; `make ci` stays green.
