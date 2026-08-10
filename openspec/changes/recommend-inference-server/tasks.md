## 1. Catalog + ranking — PR-K

- [ ] 1.1 Expand `servers.py` catalog (MLX, llama-server, Jan, oobabooga, llamafile, gpt4all, SGLang, TensorRT-LLM) with research-verified format/backends; add per-server `rank` hints and `reason` templates
- [ ] 1.2 `recommend_servers(model, category)` in servers.py (format × backends × rank policy) + Python tests (NVIDIA/GGUF, Mac/safetensors, exclusions)
- [ ] 1.3 Frontend: hardware-aware details recommendation (badges + category picker) + wizard per-pick suggestions; expand JS SERVERS mirror
- [ ] 1.4 jsdom tests: recommendation + badges + wizard suggestions/filter
- [ ] 1.5 Gate: pytest, jsdom, Playwright, openspec validate; README/AGENTS touch if user-facing surface changes
