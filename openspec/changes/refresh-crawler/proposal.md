# Refresh crawler (update existing models) + trending split

## Why

The crawler only fetches *trending* models. The user wants the existing committed
models to stay fresh too: a `make refresh` command that re-fetches each model's HF
metadata (downloads, trending, license, context window, languages, benchmarks,
profile) and updates the files in place — while `make crawl` stays the trending
crawler. Refresh preserves quants + hardware flags (file sizes are stable) and
re-runs the enrichment so every derived field (including the profile) tracks the
live README/config.

## Requirements

- ADDED: `--refresh` mode in the crawler CLI: reads existing model files (--in,
  default --out), re-fetches details, updates volatile fields, re-enriches,
  validates, emits. Artifacts (index.json/meta.json) are never treated as models.
- ADDED: `make refresh` target (nerdctl, host network, models+data mounts) —
  separate from `make crawl` (trending).
- Preserved: quants + hardware flags stay byte-identical unless the model itself
  changed (no re-derivation in refresh).
- Tests both sides: hermetic refresh tests (mocked HF: downloads/trending update,
  quants/hardware preserved, profile rebuilt, schema-valid emit) + Makefile
  dry-run test for the refresh target.
