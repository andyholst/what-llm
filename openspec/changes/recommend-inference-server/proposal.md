# Recommend the inference server per model × hardware

## Why

Issue #27 shipped a flat per-model `servers[]` list — every GGUF model shows the
same four servers regardless of hardware, and vLLM/TGI/MLX never appear for GGUF
models. The user's ask: **"I should be suggested which inference server I can use,
based on the LLM model I choose AND my hardware."** So the feature becomes a
recommendation engine: for a given (model, hardware) pair, suggest the best server
with a reason (easiest / fastest / most control / Apple-native), validated against
model format × backend support.

Verified server/hardware facts land from research (deleg_18d891c7, 2026-08-10);
the catalog is expanded with MLX, llama-server, Jan, oobabooga, llamafile, gpt4all,
SGLang, TensorRT-LLM as supported by evidence.

## Requirements

- ADDED: `recommend_servers(model, hardware_category)` — ranked list of
  {name, tier (recommended|alternative), reason}, computed from model format ×
  backend matrix × rank policy.
- ADDED: details pane shows a hardware-aware recommendation (model detail has no
  hardware selector → show "Recommended: X (easiest)" plus alternatives with
  backend badges, using the default/most-common category or a hardware picker).
- ADDED: wizard picks render the suggested server + reason per pick; the server
  select still filters.
- MODIFIED: catalog expanded (MLX etc.) with accurate format/backend data from
  research; GGUF vs safetensors handling per evidence (vLLM GGUF status).
- Tests both sides: Python ranking/matrix tests; jsdom recommendation + badge
  tests.
