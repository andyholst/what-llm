# Verify Apple memory tiers (current-gen configs)

## Why

PR-P shipped Apple tiers with M2/M3-era entries (MacBook 32/96, Mac Studio 32/256,
Mac Mini missing 36/64). The user: "macbook pro can have lower than 192 GB too…
check all the models carefully" + "macbook pro can have 48 GB too… did you do your
research?!"

Verified 2026-08-10 against Apple spec pages (support.apple.com/en-us/126318 etc.):
- MacBook Pro (M5 Pro/M5 Max): M4 16, M4/M5 Pro 24/48, M5 Max 36 → 48/64/128 →
  `[16, 24, 36, 48, 64, 128]` (M3-era 32/96 removed)
- Mac Mini (M4/M4 Pro/M4 Max): 16/24/32 + M4 Max 36/64/128 → `[16, 24, 32, 36, 48, 64, 128]`
- Mac Studio (M4 Max/M3 Ultra): M4 Max 36/64/128, M3 Ultra 96/192/384/512 →
  `[36, 64, 96, 128, 192, 384, 512]` (M2-era 32/256 removed)
- Mac Pro (M3 Ultra): 192/384/512 — unchanged

## Requirements

- ADDED: correct tier constants per the verified table (estimator), matching schema
  keys, frontend TIERS, regenerated samples.
- ADDED: every Apple tier pinned by tests on BOTH sides — estimator asserts exact
  flags for 8B/46.7B/72.7B/671B/304B-class models across all four Mac sections;
  jsdom asserts exact box counts per section; refresh-crawler fixtures use the new
  key sets.
