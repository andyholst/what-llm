# Inference-server catalog (run this model locally with…)

## Why

A model that "fits" is only half the story — the user must also know WHICH local
inference server can run it on their hardware, and how to get it. llama.cpp and
Ollama (GGUF), vLLM (safetensors/AWQ/GPTQ), LM Studio and koboldcpp (GGUF) have
different backends (CUDA / ROCm / Metal / SYCL+Vulkan / CPU) and different URLs.
The wizard should filter by server; the details pane should link to each server.

Backends verified 2026-08-10 against llama.cpp README, docs.ollama.com/gpu,
docs.vllm.ai (see `RESEARCH-backends-criteria.md`).

## Requirements

- ADDED: a curated server catalog: name, URL, model format(s), backend coverage per
  hardware category, notes. Initial: llama.cpp, Ollama, vLLM, LM Studio, koboldcpp,
  TGI.
- ADDED: contract field `servers[]` (names) per model, computed by the crawler:
  GGUF quants → GGUF servers (llama.cpp/Ollama/LM Studio/koboldcpp); safetensors →
  vLLM/TGI; empty if unknown.
- ADDED: details pane "Run locally with" chips linking to each server's site.
- ADDED: wizard gains a server filter: picks only models runnable with the selected
  server on the selected hardware category (backend coverage).
- Tests both sides: Python catalog/matrix tests; jsdom wizard filter + chip tests.
