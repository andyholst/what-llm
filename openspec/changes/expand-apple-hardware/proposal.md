# Mac Mini + Mac Pro sections + agentic-coding capability

## Why

The hardware list covered NVIDIA/AMD/Arc/Snapdragon/MacBook/Mac Studio/DGX/phones —
but the popular Apple desktops were missing: **Mac Mini** (M4 16 → M4 Max 128 GB
unified) and **Mac Pro** (M3 Ultra 192/384/512 GB). Users buying an agentic-coding
machine want to see these machines AND know whether a model can actually drive
agentic coding (coding/reasoning capability + long context).

Verified 2026-08-10 (Apple spec pages + industry): Mac Mini M4 16 GB, M4 Pro
24/48 GB, M4 Max 32/64/128 GB; Mac Pro M3 Ultra 192/384/512 GB — both unified
memory (usable = tier − 3.5 GB, like all Macs).

## Requirements

- ADDED: `mac_mini` section (16/24/32/48/64/128) + `mac_pro` section
  (192/384/512), unified-memory math, Metal backend, in estimator/schema/frontend
  (hardware filter + wizard).
- ADDED: `agentic_capable(best_for, context_window)` — coding/reasoning/agentic
  model AND ≥32K context; surfaced as a wizard checkbox filter + an "Agentic
  coding ready" badge in the details pane and per wizard pick.
- Tests both sides: estimator tier pins + agentic unit tests; jsdom 11-section box
  counts + Mac Mini/Pro wizard parity + agentic filter/badge.
