# what-llm

What LLM can my hardware actually run?

A two-part project:

1. **Python crawler** (`crawl_models.py`) — fetches currently trending models from
   Hugging Face, extracts metadata (parameters, dense/MoE architecture, GGUF quants,
   downloads), estimates VRAM per quant, and writes **one strict-contract JSON file per
   model** into `models/` (plus `index.json` / `index.js` / `bundle.js`).
2. **Single-file vanilla frontend** (`index.html`) — search, model cards, quant
   selector, and NVIDIA / AMD / MacBook / mobile hardware boxes that turn green/grey
   live from the selected quant (`est. VRAM + 1.5 GB ≤ device`).

Everything runs through **nerdctl** with a Dockerfile (deps installed in-image) and
bind-mounted volumes so the JSON output persists on the host.

## Status

In construction — spec-driven via OpenSpec (`openspec/changes/add-hf-model-pipeline`).
See `AGENTS.md` for the behavior contract. Licensed under the **Apache License 2.0**.

## Quickstart (host with rootless nerdctl)

```sh
make build            # nerdctl build
make crawl LIMIT=150  # run the crawler, output into ./models
make serve            # http://localhost:8000
```

More details land with the containerization milestone.
