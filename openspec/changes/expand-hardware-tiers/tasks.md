## 1. Contract & estimator — ships as PR-2b

- [x] 1.1 Update `schemas/model.schema.json`: macbook tiers 16/24/32/48/64/96/128; add mac_studio (32/64/96/128/192/256/512) and dgx (640/1128/1440); replace mobile with android (8/12/16/24 + note) and iphone (8/12 + note); nvidia/amd unchanged
  - [ ] Verify: schema v2 loads; old mobile-keyed records FAIL; new records validate
- [x] 1.2 Update `tests/test_schema.py` for v2 (required keys, tier shapes, mobile rejected)
  - [ ] Verify: `pytest tests/test_schema.py -q` green
- [x] 1.3 Update `src/whatllm/estimator.py`: MACBOOK_TIERS 16..128, MAC_STUDIO_TIERS, DGX_TIERS, ANDROID_TIERS, IPHONE_TIERS; mac_studio uses unified − 3.5; dgx raw tiers; android/iphone practical rule kept (≤4 B + fits 8 GB)
  - [ ] Verify: 70B Q4_K_M est 45.8 → MacBook 64/96/128 green, 48 grey; Mac Studio 64 green; DeepSeek-R1 671B → only DGX green; phones grey + note
- [x] 1.4 Update `tests/test_estimator.py` (new tier tables, Mac Studio/DGX fits, phone practicality, multi-GPU note now DGX-only path)
  - [ ] Verify: `pytest tests/test_estimator.py -q` green
- [x] 1.5 Commit, push branch, PR-2b, CI green, merge
  - [ ] Verify: CI passes on PR-2b; PR merged

## 2. Sample data — ships as PR-3

- [x] 2.1 Regenerate `models/` with v2 flags; ADD 6 more models (Llama-3.2-1B, Qwen2.5-3B, Gemma-3-4B, Qwen3-32B, Llama-3.1-70B, DeepSeek-V4-Flash-0731-GGUF 304B MoE with real quant sizes) — 14 total, exercising every category
  - [x] Verify: all schema-v2-valid; invariant recompute(quants[0]) == hardware{} holds; node --check on index.js/bundle.js
- [x] 2.2 Commit, push branch, PR-3, CI green, merge
  - [x] Verify: CI passes on PR-3; PR merged

## 3. Frontend — ships as PR-4

- [x] 3.1 Update `index.html`: sections Mac Studio, DGX, Android, iPhone; MacBook 7 tiers; TIERS map with mac subtract for macbook + mac_studio; android/iphone boxes + note
  - [x] Verify: served page renders all sections for sample data; quant switch flips boxes
- [x] 3.2 Update `tests/frontend.test.mjs` (new sections, extreme MoE shows DGX-only, 70B shows MacBook 64+ green)
  - [x] Verify: `npm test` green locally and in CI
- [x] 3.3 Commit, push branch, PR-4, CI green, merge
  - [x] Verify: CI passes on PR-4; PR merged
