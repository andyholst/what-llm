# RESEARCH — hardware tiers & inference backends (2026-08-10)

Verified by 5 research workers against NVIDIA/AMD/Intel/Qualcomm official pages,
llama.cpp README, docs.ollama.com/gpu, docs.vllm.ai. Issue #26.

## NVIDIA (CUDA)

| Tier GB | Anchors (verified) |
|---|---|
| 8 | RTX 5060 / 5060 Ti 8GB / 4060 / 4060 Ti 8GB |
| 12 | RTX 5070 / 4070 / 5060 Ti 16? (12: 5070, 4070) |
| 16 | RTX 5080 / 5070 Ti / 4080 / 4070 Ti Super / 5060 Ti 16GB |
| 20 | RTX 4000 Ada (workstation, ECC) |
| 24 | RTX 4090 / RTX 5000 Ada / 4500 Ada |
| 32 | **RTX 5090 (GDDR7, flagship — was MISSING)** / RTX 5000 Ada |
| 48 | RTX 6000 Ada / A6000 |
| 96 | **RTX PRO 6000 Blackwell (workstation — was MISSING)** |
| 80 / 192 | H100 / B200 (cloud/datacenter → DGX section) |

Compute capability: Ada 8.9, consumer/workstation Blackwell 12.0, Hopper 9.0,
datacenter Blackwell 10.0. B200 = 192 GB HBM3e (B100 = 180 GB — a Civo source error
caught and corrected). 50-Super cards are leak-only → not listed.

## AMD (ROCm; ROCm 7.x officially supports RX 9000/7000 + Radeon PRO)

| Tier GB | Anchors |
|---|---|
| 8 | RX 7600 / 9060 / 9060 XT 8GB |
| 12 | RX 7700 XT |
| 16 | RX 9070 XT / 9070 / 9060 XT 16GB / 7800 XT / 7900 GRE |
| 20 | **RX 7900 XT (was MISSING)** |
| 24 | RX 7900 XTX |
| 32 | Radeon PRO W7800 |
| 48 | Radeon PRO W7900 / W7800 48GB refresh |
| 192 | Instinct MI300X (datacenter) |

## Intel Arc (SYCL/oneAPI + Vulkan — production in llama.cpp/Ollama)

| Tier GB | Anchors |
|---|---|
| 8 | Arc A750 |
| 10 | Arc B570 |
| 12 | Arc B580 |
| 16 | Arc A770 (B770 cancelled — not listed) |

## Qualcomm Snapdragon X (unified memory like macOS: usable = tier − 3.5)

| Tier GB | Notes |
|---|---|
| 16 / 32 / 64 | X Elite / X Plus / X2 laptops (shipped configs; X2 128 GB is leak-only). NPU 45–80 TOPS; local LLM via CPU + Adreno Vulkan (no first-class NPU path in llama.cpp; OpenVINO NPU backend WIP). |

## Inference backends (the "criteria" beyond VRAM)

- **CUDA** (NVIDIA): production in llama.cpp/Ollama/vLLM.
- **ROCm** (AMD): production in llama.cpp/Ollama/vLLM (RX 7900/9000 + PRO + Instinct).
- **Metal** (Apple): production in llama.cpp/Ollama.
- **SYCL/oneAPI + Vulkan** (Intel Arc): production in llama.cpp/Ollama (Vulkan is how Arc runs in Ollama); partial vLLM (XPU).
- **Vulkan** (any GPU): llama.cpp default offload on ARM64 Linux; Ollama supports.
- **NPU** (Qualcomm/Intel AI Boost): emerging — OpenVINO backend in llama.cpp is WIP (text-only); Ollama has NO NPU backend.
- **CPU**: always available.

## Hugging Face criteria

HF publishes memory-math guidance (params ×2 GB fp16, 4-bit tables, KV-cache math,
`accelerate estimate-memory`, blog per-model VRAM numbers) — NOT a hardware tier
list. Decision: fit math stays VRAM-based (HF-backed formulas), tier NAMES come from
the manufacturer lineups above, backend labels shown per section on the page.

## Links (primary)

- https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/ (32 GB)
- https://www.amd.com/en/products/graphics/desktops/radeon/7000-series/amd-radeon-rx-7900xt.html (20 GB)
- https://www.intel.com/content/www/us/en/products/details/discrete-gpus/arc/desktop/b-series.html
- https://www.qualcomm.com/laptops/products/snapdragon-x-elite
- https://github.com/ggml-org/llama.cpp (backends list)
- https://docs.ollama.com/gpu · https://docs.vllm.ai/en/stable/getting_started/installation/gpu/
- https://huggingface.co/docs/transformers/llm_tutorial_optimization (memory math)
