## ADDED Requirements

### Requirement: Refresh mode
`python -m whatllm.crawl_models --refresh [--out DIR] [--in DIR]` MUST update the
existing per-model files: re-fetch each model's HF detail (with the full expand
set), refresh downloads / trending_score / name / author / license / context /
languages / benchmarks / servers / profile / last_updated, and MUST preserve the
existing `quants` and `hardware` fields. `--in` MUST default to `--out`.
Artifacts (index.json, meta.json) MUST be skipped, never treated as models.

#### Scenario: metadata refresh
- **WHEN** `--refresh` runs against a dir of model files
- **THEN** downloads/trending come from the fresh detail response, `last_updated`
  is today, the profile is rebuilt from the fresh README, and quants + hardware
  flags are unchanged
- **AND** every updated record passes the schema; index/bundle artifacts are
  re-emitted

### Requirement: Makefile split
`make refresh` MUST run the crawler with `--refresh` (nerdctl, host network,
models + data bind mounts). `make crawl` MUST keep its trending behavior.

#### Scenario: dry-run gate
- **WHEN** `make -n refresh` runs
- **THEN** the command carries `--refresh --out /app/models --in /app/models`
  plus `--network host` and the bind mounts

### Requirement: Hermetic tests
Refresh MUST be tested without network: mocked detail/README/config responses
drive a seeded model file; assertions cover field updates, preservation of
quants/hardware, schema validity, and artifact emission. The Makefile test MUST
cover the new target.

#### Scenario: gate runs
- **WHEN** pytest runs
- **THEN** refresh tests pass against the mocked fixtures
