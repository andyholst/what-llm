# Expand hardware manufacturers (real 2026 GPU landscape)

## Why

The NVIDIA section stops at 48 GB and AMD at 24 GB — but the current flagship
**RTX 5090 has 32 GB**, workstation cards go 20/48/**96 GB** (RTX 4000 Ada, RTX 6000
Ada, RTX PRO 6000 Blackwell), AMD ships 20 GB (RX 7900 XT), 48 GB (Radeon PRO W7900)
and 192 GB (Instinct MI300X), and Intel Arc (8-16 GB) + Snapdragon X laptops
(16/32/64 GB unified) are now real local-LLM targets. Users shopping for "which LLM
can I run" deserve tiers that match what they can actually buy, plus the backend
criteria (CUDA / ROCm / Metal / SYCL+Vulkan / NPU) per category.

All figures verified 2026-08-10 against NVIDIA/AMD/Intel/Qualcomm official pages
(research: 5 workers, URL-cited; also `RESEARCH-hardware-tiers.md` in the repo).

## Requirements

- ADDED: NVIDIA tiers 8, 12, 16, 20, 24, 32, 48, 96 GB (anchors: RTX 5060/4060 →
  RTX 5090 → RTX 4000 Ada → RTX PRO 6000 Blackwell).
- ADDED: AMD tiers 8, 12, 16, 20, 24, 32, 48, 192 GB (RX 7600 → RX 7900 XT →
  W7900 → MI300X), ROCm-backed.
- ADDED: Intel Arc section (8, 10, 12, 16 GB; A750/A570→A770/B580), SYCL+Vulkan.
- ADDED: Snapdragon X section (16, 32, 64 GB unified, −3.5 GB system overhead like
  Macs; CPU/Adreno Vulkan; NPU emerging).
- MODIFIED: every hardware category in the UI labels its inference backend(s)
  (NVIDIA=CUDA, AMD=ROCm, Mac=Metal, Arc=SYCL/Vulkan, Snapdragon=CPU/Vulkan,
  DGX=CUDA, phones=CPU).
- Tests both sides: Python estimator pins per tier set; jsdom box counts + wizard
  parity for the new sections.
