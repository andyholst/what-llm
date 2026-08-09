# Extend Model Metadata (model profile + license + context + taxonomy)

## Why

Users must be able to answer "which LLM should I use for MY need?" — and today the
contract answers "does it fit?" but not "what is it good for, and what are its limits?".
The user explicitly wants the model description to surface **best use cases,
strengths, weaknesses, and limitations**, and requires that **the Python crawler
derives these programmatically** (not hand-written notes).

Research (skeptic-verified, live HF probes 2026-08-10):
- HF exposes license (`cardData.license`), base_model (`cardData.base_model`, a LIST),
  sparse `evalResults`, ISO language tags — but NO description/use-case field, NO
  context length in `expand[]=config` (only architectures/model_type/tokenizer_config;
  the raw `config.json` has `max_position_embeddings`), and NO knowledge cutoff anywhere.
- READMEs are the only human text; sections are org-specific (`## Model Overview`,
  `## Limitations`, `### Intended use`) and gated models 401 (gate on `gated != false`).
- Enrichment budget: list+detail+tree+README+config = 482 req / 150 models = 96% of the
  anonymous 500 req / 5-min fixed window → needs pacing + resume (both already exist).

## What Changes

- `schemas/model.schema.json` v3 gains: `profile {summary, best_for[], strengths[],
  weaknesses[], limitations[], provenance[]}`, `license`, `commercial_ok`,
  `context_window`, `model_type`, `languages[]`, `knowledge_cutoff`, `benchmarks[]`.
- New `src/whatllm/profile.py`: Python-derived profile extraction — README section
  mining + structured inference (evals → strengths, context → capability, license →
  limitation, tags → languages/vision) + curated family fallback; every claim carries
  provenance (source + confidence).
- Crawler enrichment steps (all gated + budgeted): README fetch (skip when
  `gated != false`), raw `config.json` fetch (context window), cardData expand (license,
  base_model).
- Frontend: profile panel (best-for chips, strengths/weaknesses/limitations lists with
  provenance), license/context/use-case filters, freshness indicator.

## Capabilities

- C1: Python-derived model profile (best_for / strengths / weaknesses / limitations
  with provenance).
- C2: License + commercial-use gate.
- C3: Context window.
- C4: Model-type taxonomy (base/instruct/chat/reasoner/vision).
- C5: Languages + best-effort knowledge cutoff.
- C6: Best-effort benchmarks (verified flag surfaced honestly).
- C7: Rate-aware enrichment (≤ 500 req / 5 min, gated-model skipping, resume).

## Impact

- Contract: breaking addition (schema v3) — samples + frontend + tests regenerate.
- Crawler: +2–3 requests/model, one new module, no new dependencies.
- Frontend: profile panel + filters; index summary gains freshness timestamp.
- Docs: AGENTS.md + README updated (new fields, gating rules, budget math).
