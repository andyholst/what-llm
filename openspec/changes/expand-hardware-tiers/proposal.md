# Expand Hardware Tiers

## Why

The user asked for real-world hardware coverage beyond consumer GPUs and a generic
"mobile" flag: **Android/Samsung phones, iPhone, Mac Studio, NVIDIA DGX**, and MacBook
tiers up to the **128 GB unified memory** that the Apple M5 Max supports (verified on
Apple's official spec pages, 614 GB/s). The single `mobile{practical,note}` category is
too coarse — an S25 Ultra (12/16 GB) and an iPhone 17 Pro (12 GB) are different targets.

## What Changes

- `schemas/model.schema.json` (MODIFIED): `hardware` gains `mac_studio` and `dgx` tier
  maps, `macbook` tiers extend to 16/24/32/48/64/96/128 GB, and `mobile` is **replaced**
  by `android` (8/12/16/24 GB + note) and `iphone` (8/12 GB + note). `nvidia`/`amd`
  unchanged.
- `src/whatllm/estimator.py` (MODIFIED): tier constants for the new categories;
  Mac Studio uses unified-memory math (usable = tier − 3.5, like MacBook); DGX uses raw
  system GPU-memory tiers (640/1128/1440 GB total — DGX A100/H100/H200/B200-class);
  Android/iPhone keep the practicality rule (params ≤ 4 B and smallest quant fits 8 GB)
  plus per-tier fit flags.
- Sample dataset grows (6 more models: 1 B → 304 B MoE GGUF) so every new category is
  exercised, including a DGX-only extreme MoE.
- `index.html` (MODIFIED): new hardware sections (Mac Studio, DGX, Android, iPhone) and
  MacBook tiers through 128 GB; boxes still flip from the selected quant via
  `est + 1.5 ≤ tier` (Mac categories: `tier − 3.5` usable).

## Capabilities

- `model-pipeline` (MODIFIED): hardware compatibility now spans consumer GPUs, Apple
  laptops and workstations, datacenter DGX systems, and the two phone platforms.

## Impact

- Breaking contract change: `mobile` removed → frontend, samples, and tests updated in
  the same delivery; old `models/*.json` regenerated.
- Facts sourced: Apple M5/Mac Studio spec pages, NVIDIA DGX docs, GSMArena/Samsung
  (S25 Ultra 12/16 GB, iPhone 17 Pro 12 GB). Heuristics (unified −3.5, phone ≤4 B)
  remain labeled heuristics.
- Future candidates noted (not in scope): Snapdragon X Elite laptops, Intel Arc.
