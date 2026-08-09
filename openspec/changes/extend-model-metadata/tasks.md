## 1. Contract & schema — ships PR-A

- [ ] 1.1 `schemas/model.schema.json` v3: add `profile` (summary, best_for[], strengths[], weaknesses[], limitations[], provenance[]), `license`, `commercial_ok`, `context_window`, `model_type`, `languages[]`, `knowledge_cutoff` (nullable), `benchmarks[]`
  - [ ] Verify: good/bad records; schema tests updated (mobile-era records still reject; v3 fields required)
- [ ] 1.2 `tests/test_schema.py` v3 cases (profile shape, provenance entries, benchmarks verified flag, nullable knowledge_cutoff)
  - [ ] Verify: pytest green

## 2. Profile extraction module — ships PR-B

- [ ] 2.1 `src/whatllm/profile.py`: README fetch (skip when `gated != false` from API — no 401 probing), YAML frontmatter parse, section mining with normalized headings (Limitations / Weaknesses / Strengths / Intended Use(s) / Use cases / What is this / Model Overview)
  - [ ] Verify: hermetic fixtures (Qwen-style + DeepSeek-style READMEs, gated + ungated)
- [ ] 2.2 structured inference: evalResults list entries → strength candidates (dataset + value + verified flag); context window → capability note; license → limitation; ISO tags → languages
  - [ ] Verify: unit tests for each signal; provenance recorded
- [ ] 2.3 curated family fallback map (Qwen/Mistral/Llama/DeepSeek/Phi/…) used when README gated/absent; claims tagged `source: curated`
  - [ ] Verify: gated fixture falls back cleanly; confidence values present
- [ ] 2.4 `tests/test_profile.py` hermetic suite (no network)
  - [ ] Verify: pytest green

## 3. Crawler enrichment — ships PR-B

- [ ] 3.1 crawler: fetch README + raw `config.json` per kept model, gated-model skip, budget accounting (482 req / 150 models ≈ 96% of 500/5-min window — keep 0.6 s pacing, reuse resume checkpoint)
  - [ ] Verify: mocked HTTP tests assert request counts and gating; resume skips done
- [ ] 3.2 contract assembly: license (cardData.license or `license:*` tag), commercial_ok (curated NC denylist), context_window (max_position_embeddings → n_positions → sliding_window fallback), model_type (cardData.base_model LIST + id-suffix heuristics + overrides), languages, knowledge_cutoff (README prose, null default), benchmarks (evalResults LIST, verified:false default)
  - [ ] Verify: unit tests; DeepSeek-Coder example uses `gated=false` not 401
- [ ] 3.3 `tests/test_crawler_enrich.py` hermetic suite
  - [ ] Verify: pytest green

## 4. Samples & frontend — ships PR-C

- [ ] 4.1 regenerate 14 samples with v3 profile (hand-curated profiles consistent with real model families) + freshness timestamp in index
  - [ ] Verify: schema + invariant + node --check
- [ ] 4.2 frontend: profile panel (best-for chips, strengths/weaknesses/limitations with provenance tooltip), license badge + filter, context window display + filter, model-type badge, freshness indicator
  - [ ] Verify: jsdom + Playwright tests (profile renders, filters work, freshness shown)
- [ ] 4.3 index summary gains `profile` subset + `crawled_at`; file:// bundle unaffected
  - [ ] Verify: node --check; jsdom passes

## 5. Docs & gate

- [ ] 5.1 AGENTS.md: new fields, gating rule (`gated != false`), budget math, provenance honesty rules
- [ ] 5.2 ci.yaml node container validates `extend-model-metadata` too
  - [ ] Verify: openspec validate green for all 4 changes; `make ci` green
- [ ] 5.3 final: tick all boxes, PRs merged, report

## 6. Speed decision — ships PR-D (decision required first)

- [ ] 6.1 Decide: `est_tok_s` per hardware tier from a curated device-bandwidth table (memory bandwidth ÷ model bytes, honest approximation) vs explicit null default; document "no per-user-hardware structured source" (Artificial Analysis exists but is not machine-readable per arbitrary hardware)
  - [ ] Verify: decision recorded in AGENTS.md; contract field (if approved) with tests
