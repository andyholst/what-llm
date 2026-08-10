## 1. Catalog + contract — PR-J

- [ ] 1.1 `src/whatllm/servers.py`: SERVER_CATALOG (llama.cpp, Ollama, vLLM, LM Studio, koboldcpp, TGI) with url/format/backends/notes
- [ ] 1.2 `schema`: add `servers[]` (required, strings); samples regenerate valid
- [ ] 1.3 Crawler/make_samples: compute `servers` from quants (gguf vs safetensors)
- [ ] 1.4 Frontend: details pane "Run locally with" chips (links) + wizard server select + backend-aware filtering
- [ ] 1.5 Python tests: catalog + matrix + per-model computation
- [ ] 1.6 JS tests: chips + links + wizard server filter parity
