## ADDED Requirements

### Requirement: Recommendation engine
A function MUST return a ranked server recommendation for a (model, hardware)
pair: `[{name, tier: "recommended"|"alternative", reason}]`. Candidates MUST pass
model-format match AND backend coverage for the hardware category. Rank policy:
easiest (Ollama/LM Studio) > fastest (vLLM/TGI) > most-control (llama.cpp) >
platform-native (MLX on Apple).

#### Scenario: NVIDIA + GGUF model
- **WHEN** a GGUF model is matched against NVIDIA
- **THEN** the recommendation lists Ollama (easiest, CUDA) and llama.cpp (most
  control, CUDA), and does NOT list MLX

#### Scenario: MacBook + safetensors model
- **WHEN** a safetensors model is matched against MacBook
- **THEN** MLX appears (Apple-native) alongside llama.cpp alternatives, and
  TensorRT-LLM does NOT appear

### Requirement: Hardware-aware details pane
The details pane MUST show "Recommended: X — reason" plus alternatives with
backend badges (CUDA / ROCm / Metal / SYCL+Vulkan / CPU) per hardware category,
with a category picker when no hardware is selected.

#### Scenario: chip badges
- **WHEN** a model detail renders
- **THEN** each server chip carries its backend badge for the chosen category

### Requirement: Wizard suggestions
Each wizard pick MUST render its suggested server + reason; the server select
filter MUST keep working against the expanded catalog.

#### Scenario: picks show suggestions
- **WHEN** the wizard returns picks for NVIDIA 24 GB
- **THEN** every row shows a suggested server with a reason, and all candidates
  pass format × backend × fit

### Requirement: Expanded catalog
The catalog MUST include MLX, llama-server, Jan, oobabooga, llamafile, gpt4all,
SGLang and TensorRT-LLM with format/backend data verified by research, plus the
existing six.

#### Scenario: catalog size
- **WHEN** the catalog is rendered
- **THEN** it has at least 12 entries, each with URL, format and backends

### Requirement: Hermetic tests
- Python: recommendation ranking (NVIDIA/Mac cases above), format × backend
  exclusion, catalog completeness.
- JS: details recommendation + badges; wizard suggestions + filter.

#### Scenario: gate runs
- **WHEN** CI runs pytest and jsdom
- **THEN** all recommendation tests pass against committed data
