## ADDED Requirements

### Requirement: Server catalog
A curated catalog MUST exist with at least: llama.cpp, Ollama, vLLM, LM Studio,
koboldcpp, TGI. Each entry MUST have `name`, `url`, `format` (gguf | safetensors |
both), `backends` (per hardware category), `notes`.

#### Scenario: llama.cpp entry
- **WHEN** the catalog is rendered
- **THEN** llama.cpp links to https://github.com/ggml-org/llama.cpp with
  format gguf and backends cuda/rocm/metal/vulkan/sycl/cpu

#### Scenario: vLLM entry
- **WHEN** the catalog is rendered
- **THEN** vLLM links to https://docs.vllm.ai with format safetensors and
  backends cuda/rocm (no vulkan)

### Requirement: Per-model servers field
Every model file MUST include `servers[]` (array of catalog names). A model with
GGUF quants MUST include the GGUF servers; a safetensors model MUST include
vLLM/TGI; unknown → empty array.

#### Scenario: GGUF model
- **WHEN** a model has gguf quants
- **THEN** its `servers` include llama.cpp, Ollama, LM Studio and koboldcpp

### Requirement: Details pane links
The details pane MUST render "Run locally with" chips for the model's servers,
each linking to the server's URL.

#### Scenario: clickable server
- **WHEN** a user opens a model with servers
- **THEN** a chip per server appears, linking out to its site

### Requirement: Wizard server filter
The wizard MUST offer a server select; picks MUST be restricted to models whose
servers include the chosen server AND whose backend covers the chosen hardware
category.

#### Scenario: filter by server
- **WHEN** a user picks Ollama + NVIDIA 12 GB
- **THEN** every pick is GGUF, fits 12 GB, and runs on Ollama (CUDA)

### Requirement: Hermetic tests
Tests MUST cover the catalog and the wizard filter without network:
- Python: catalog completeness, backend matrix sanity (vLLM has no vulkan; Ollama
  has no NPU), per-model server computation (GGUF vs safetensors).
- JS: chips render + link; wizard server filter restricts picks.

#### Scenario: gate runs
- **WHEN** the CI gate runs pytest and jsdom
- **THEN** catalog/matrix/filter tests pass against the committed data
