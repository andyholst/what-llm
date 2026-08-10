"""Inference-server catalog + recommendation engine (issue #27, #30).

Which LOCAL server can run a given model on a given hardware category — and
WHICH ONE you should pick. Backends verified 2026-08-10 against llama.cpp README,
docs.ollama.com/gpu, docs.vllm.ai, rocm.docs.amd.com, nvidia.github.io/TensorRT-LLM
(see RESEARCH-hardware-tiers.md; research deleg_18d891c7).

The catalog is curated and static. `servers_for_model()` computes the contract
`servers[]` field from quant names (format only). `recommend_servers()` ranks the
usable servers for a (model, hardware) pair with a reason per pick.
"""
from __future__ import annotations

# tier: prod (production-grade everywhere) | desktop (great for local desktop use)
#       | experimental (works but rough) | hobby (limited: gpt4all 2k ctx)
SERVERS: list[dict] = [
    {
        "name": "llama.cpp",
        "url": "https://github.com/ggml-org/llama.cpp",
        "format": "gguf", "tier": "prod",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "SYCL/Vulkan", "snapdragon": "CPU/Vulkan", "dgx": "CUDA",
            "android": "CPU", "iphone": "CPU",
        },
        "notes": "Reference GGUF server; broadest backend support incl. Vulkan + WIP OpenVINO NPU",
    },
    {
        "name": "llama-server",
        "url": "https://github.com/ggml-org/llama.cpp/tree/master/tools/server",
        "format": "gguf", "tier": "desktop",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "SYCL/Vulkan", "snapdragon": "CPU/Vulkan", "dgx": "CUDA",
            "android": None, "iphone": None,
        },
        "notes": "llama.cpp's own OpenAI-compatible server",
    },
    {
        "name": "Ollama",
        "url": "https://ollama.com",
        "format": "gguf", "tier": "desktop",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "Vulkan", "snapdragon": "CPU", "dgx": "CUDA",
            "android": None, "iphone": None,
        },
        "notes": "Easiest install (one command); no NPU backend yet",
    },
    {
        "name": "LM Studio",
        "url": "https://lmstudio.ai",
        "format": "gguf", "tier": "desktop",
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
        "format": "gguf", "tier": "desktop",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "Vulkan", "snapdragon": "CPU", "dgx": "CUDA",
            "android": None, "iphone": None,
        },
        "notes": "Story/creative-writing focused GGUF server",
    },
    {
        "name": "Jan",
        "url": "https://jan.ai",
        "format": "gguf", "tier": "desktop",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "Vulkan", "snapdragon": "CPU", "dgx": "CUDA",
            "android": None, "iphone": None,
        },
        "notes": "Desktop app with llama.cpp engine",
    },
    {
        "name": "oobabooga",
        "url": "https://github.com/oobabooga/textgen",
        "format": "gguf", "tier": "desktop",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "Vulkan", "snapdragon": "CPU", "dgx": "CUDA",
            "android": None, "iphone": None,
        },
        "notes": "text-generation-webui: desktop UI with many loaders",
    },
    {
        "name": "llamafile",
        "url": "https://github.com/Mozilla-Ocho/llamafile",
        "format": "gguf", "tier": "desktop",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "Vulkan", "snapdragon": "CPU", "dgx": "CUDA",
            "android": "CPU", "iphone": None,
        },
        "notes": "Single-file executable (model + runtime bundled)",
    },
    {
        "name": "gpt4all",
        "url": "https://www.nomic.ai/gpt4all",
        "format": "gguf", "tier": "hobby",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "macbook": "Metal", "mac_studio": "Metal",
            "intel_arc": "Vulkan", "snapdragon": "CPU", "dgx": "CUDA",
            "android": None, "iphone": None,
        },
        "notes": "Easy GUI; ~2k context limit (hobby)",
    },
    {
        "name": "vLLM",
        "url": "https://docs.vllm.ai",
        "format": "safetensors", "tier": "prod",
        "backends": {
            "nvidia": "CUDA", "amd": "ROCm", "dgx": "CUDA", "intel_arc": "XPU",
            "macbook": None, "mac_studio": None, "snapdragon": None,
            "android": None, "iphone": None,
        },
        "notes": "High-throughput (AWQ/GPTQ/FP8/Marlin); GGUF load = experimental plugin, ~8x slower",
    },
    {
        "name": "TGI",
        "url": "https://huggingface.co/docs/text-generation-inference",
        "format": "safetensors", "tier": "prod",
        "backends": {
            "nvidia": "CUDA", "amd": None, "dgx": "CUDA", "intel_arc": None,
            "macbook": None, "mac_studio": None, "snapdragon": None,
            "android": None, "iphone": None,
        },
        "notes": "Hugging Face's server; consumer AMD unsupported (Instinct only)",
    },
    {
        "name": "SGLang",
        "url": "https://github.com/sgl-project/sglang",
        "format": "safetensors", "tier": "prod",
        "backends": {
            "nvidia": "CUDA", "amd": None, "dgx": "CUDA", "intel_arc": None,
            "macbook": None, "mac_studio": None, "snapdragon": None,
            "android": None, "iphone": None,
        },
        "notes": "High-performance serving; consumer AMD unsupported (Instinct only)",
    },
    {
        "name": "TensorRT-LLM",
        "url": "https://github.com/NVIDIA/TensorRT-LLM",
        "format": "safetensors", "tier": "prod",
        "backends": {
            "nvidia": "CUDA", "dgx": "CUDA",
            "amd": None, "intel_arc": None, "macbook": None, "mac_studio": None,
            "snapdragon": None, "android": None, "iphone": None,
        },
        "notes": "NVIDIA-only, max performance (Ampere→Blackwell incl. desktop RTX)",
    },
    {
        "name": "MLX",
        "url": "https://github.com/ml-explore/mlx-lm",
        "format": "safetensors", "tier": "desktop",
        "backends": {
            "macbook": "Metal", "mac_studio": "Metal",
            "nvidia": None, "amd": None, "intel_arc": None, "snapdragon": None,
            "dgx": None, "android": None, "iphone": None,
        },
        "notes": "Apple-native (mlx-lm); safetensors/MLX format — cannot load GGUF directly",
    },
]

GGUF_SERVERS = [s["name"] for s in SERVERS if s["format"] == "gguf"]
SAFETENSORS_SERVERS = [s["name"] for s in SERVERS if s["format"] == "safetensors"]

# quant names that imply GGUF (incl. UD-/IQ* dynamic and split-file names)
_GGUF_MARKERS = ("Q2_K", "Q3_K", "Q4_K", "Q5_K", "Q6_K", "Q8_0", "IQ1", "IQ2", "IQ3",
                 "IQ4", "F16", "FP16", "BF16", "Q4_0", "Q4_1", "Q5_0", "Q5_1",
                 "TQ1", "TQ2", "TXM")

_REASON = {
    "Ollama": "easiest install (one command)",
    "LM Studio": "polished desktop GUI",
    "llama.cpp": "most control + broadest backends",
    "llama-server": "OpenAI-compatible API from llama.cpp",
    "koboldcpp": "creative/story workflows",
    "Jan": "privacy-first desktop app",
    "oobabooga": "power-user desktop UI",
    "llamafile": "single-file, zero install",
    "gpt4all": "simplest GUI (hobby, ~2k context)",
    "vLLM": "highest throughput serving",
    "TGI": "Hugging Face production server",
    "SGLang": "high-performance serving",
    "TensorRT-LLM": "maximum NVIDIA performance",
    "MLX": "Apple-native (Metal) framework",
}


def _is_gguf(quants: list[dict]) -> bool:
    if not quants:
        return False
    blob = " ".join(str(q.get("name", "")) for q in quants)
    return any(marker in blob.upper() for marker in _GGUF_MARKERS)


def servers_for_model(quants: list[dict]) -> list[str]:
    """Contract `servers[]`: format-derived (GGUF vs safetensors)."""
    if not quants:
        return []
    if _is_gguf(quants):
        return list(GGUF_SERVERS)
    return list(SAFETENSORS_SERVERS)


def recommend_servers(quants: list[dict], category: str) -> list[dict]:
    """Ranked recommendation for a (model, hardware) pair.

    Returns [{name, tier: "recommended"|"alternative", backend, reason}] — every
    entry passes format match AND backend coverage. Rank policy: platform-native
    (MLX on Apple) > easiest (Ollama) > desktop GUI (LM Studio) > control/serving.
    """
    fmt = "gguf" if _is_gguf(quants) else "safetensors"
    by = {s["name"]: s for s in SERVERS}
    candidates = []
    for name in (GGUF_SERVERS if fmt == "gguf" else SAFETENSORS_SERVERS):
        s = by[name]
        backend = s["backends"].get(category)
        if not backend:
            continue
        candidates.append({"name": name, "backend": backend, "tier": s["tier"],
                           "reason": _REASON.get(name, "")})

    # GGUF models CAN also load in vLLM (out-of-tree plugin, "highly experimental",
    # ~8x slower than Marlin) on CUDA/ROCm categories — honest alternative.
    if fmt == "gguf" and category in ("nvidia", "amd", "dgx"):
        candidates.append({"name": "vLLM", "backend": by["vLLM"]["backends"][category],
                           "tier": "experimental",
                           "reason": _REASON["vLLM"] + " (GGUF load = experimental plugin, ~8x slower)"})

    if not candidates:
        return []

    # rank: platform-native / easiest / GUI / rest, stable by catalog order
    def rank_key(c):
        if c["name"] == "MLX":
            return 0
        if c["name"] == "Ollama":
            return 1
        if c["name"] == "LM Studio":
            return 2
        return 3

    candidates.sort(key=rank_key)
    out = []
    for i, c in enumerate(candidates):
        note = ""
        if c["tier"] == "experimental":
            note = " (experimental)"
        elif c["name"] == "gpt4all":
            note = " (hobby, ~2k context)"
        out.append({
            "name": c["name"],
            "tier": "recommended" if i == 0 else "alternative",
            "backend": c["backend"],
            "reason": c["reason"] + note,
        })
    return out
