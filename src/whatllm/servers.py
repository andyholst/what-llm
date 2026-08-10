"""Inference-server catalog (inference-server-catalog, issue #27).

Which LOCAL server can run a given model on a given hardware category, with links.
Backends verified 2026-08-10 against llama.cpp README, docs.ollama.com/gpu,
docs.vllm.ai (see RESEARCH-hardware-tiers.md).

The catalog is curated and static; the per-model `servers[]` contract field is
computed from the model's quant names (GGUF-style names -> GGUF servers;
safetensors-only -> vLLM/TGI).
"""
from __future__ import annotations

SERVERS: list[dict] = [
    {
        "name": "llama.cpp",
        "url": "https://github.com/ggml-org/llama.cpp",
        "format": "gguf",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "SYCL/Vulkan", "snapdragon": "CPU/Vulkan", "dgx": "CUDA",
            "android": None, "iphone": None,
        },
        "notes": "Reference GGUF server; broadest backend support incl. Vulkan + WIP OpenVINO NPU",
    },
    {
        "name": "Ollama",
        "url": "https://ollama.com",
        "format": "gguf",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "Vulkan", "snapdragon": "CPU", "dgx": "CUDA",
            "android": None, "iphone": None,
        },
        "notes": "One-command install; no NPU backend yet",
    },
    {
        "name": "vLLM",
        "url": "https://docs.vllm.ai",
        "format": "safetensors",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "dgx": "CUDA", "intel_arc": "XPU",
            "macbook": None, "mac_studio": None, "snapdragon": None,
            "android": None, "iphone": None,
        },
        "notes": "High-throughput serving (AWQ/GPTQ); no Vulkan backend",
    },
    {
        "name": "LM Studio",
        "url": "https://lmstudio.ai",
        "format": "gguf",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "Vulkan", "snapdragon": "CPU", "dgx": "CUDA",
            "android": None, "iphone": None,
        },
        "notes": "Desktop GUI over llama.cpp",
    },
    {
        "name": "koboldcpp",
        "url": "https://github.com/LostRuins/koboldcpp",
        "format": "gguf",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "Vulkan", "snapdragon": "CPU", "dgx": "CUDA",
            "android": None, "iphone": None,
        },
        "notes": "Story/creative-writing focused GGUF server",
    },
    {
        "name": "TGI",
        "url": "https://huggingface.co/docs/text-generation-inference",
        "format": "safetensors",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "dgx": "CUDA",
            "intel_arc": None, "snapdragon": None, "macbook": None, "mac_studio": None,
            "android": None, "iphone": None,
        },
        "notes": "Hugging Face's server; CUDA-centric",
    },
]

GGUF_SERVERS = [s["name"] for s in SERVERS if s["format"] == "gguf"]
SAFETENSORS_SERVERS = [s["name"] for s in SERVERS if s["format"] == "safetensors"]

# quant names that imply GGUF (incl. UD-/IQ* dynamic and split-file names)
_GGUF_MARKERS = ("Q2_K", "Q3_K", "Q4_K", "Q5_K", "Q6_K", "Q8_0", "IQ1", "IQ2", "IQ3",
                 "IQ4", "F16", "FP16", "BF16", "Q4_0", "Q4_1", "Q5_0", "Q5_1",
                 "TQ1", "TQ2", "TXM")


def servers_for_model(quants: list[dict]) -> list[str]:
    """Compute the contract `servers[]` field from a model's quant names.

    GGUF-style quant names (Q4_K_M, UD-IQ1_M, F16, split files) -> GGUF servers
    (llama.cpp/Ollama/LM Studio/koboldcpp); anything else -> safetensors servers
    (vLLM/TGI). Unknown -> [].
    """
    if not quants:
        return []
    blob = " ".join(str(q.get("name", "")) for q in quants)
    if any(marker in blob.upper() for marker in _GGUF_MARKERS):
        return list(GGUF_SERVERS)
    return list(SAFETENSORS_SERVERS)
