"""Hermetic tests for the inference-server catalog + recommendation engine (#27, #30)."""
from __future__ import annotations

from whatllm import servers

GGUF_Q = [{"name": "Q4_K_M", "size_gb": 4.9, "estimated_vram_gb": 6.2, "notes": ""}]
SF_Q = [{"name": "full_precision", "size_gb": 16.0, "estimated_vram_gb": 17.3, "notes": ""}]


def test_catalog_completeness():
    names = {s["name"] for s in servers.SERVERS}
    assert {"llama.cpp", "Ollama", "vLLM", "LM Studio", "koboldcpp", "TGI",
            "MLX", "llama-server", "Jan", "oobabooga", "llamafile", "gpt4all",
            "SGLang", "TensorRT-LLM"} <= names
    assert len(servers.SERVERS) >= 12
    for s in servers.SERVERS:
        assert s["url"].startswith("http")
        assert s["format"] in ("gguf", "safetensors")
        assert s["tier"] in ("prod", "desktop", "experimental", "hobby")
        assert "nvidia" in s["backends"] and "snapdragon" in s["backends"]


def test_backend_matrix_sanity():
    by = {s["name"]: s for s in servers.SERVERS}
    assert by["vLLM"]["backends"]["snapdragon"] is None      # no Vulkan path
    assert by["vLLM"]["backends"]["macbook"] is None
    assert by["MLX"]["backends"]["nvidia"] is None           # Apple-only
    assert by["MLX"]["backends"]["macbook"] == "Metal"
    assert by["TensorRT-LLM"]["backends"]["amd"] is None     # NVIDIA-only
    assert by["TGI"]["backends"]["amd"] is None              # Instinct-only
    assert by["SGLang"]["backends"]["amd"] is None
    assert by["Ollama"]["backends"]["intel_arc"] == "Vulkan"


def test_gguf_quants_yield_gguf_servers():
    got = servers.servers_for_model(GGUF_Q)
    assert "llama.cpp" in got and "Ollama" in got and "LM Studio" in got
    assert "koboldcpp" in got and "vLLM" not in got and "MLX" not in got


def test_safetensors_quants_yield_vllm():
    got = servers.servers_for_model(SF_Q)
    assert "vLLM" in got and "TGI" in got and "MLX" in got
    assert "llama.cpp" not in got


def test_empty_quants_yield_empty():
    assert servers.servers_for_model([]) == []


def test_recommend_nvidia_gguf():
    rec = servers.recommend_servers(GGUF_Q, "nvidia")
    assert rec and rec[0]["tier"] == "recommended"
    assert rec[0]["name"] == "Ollama" and rec[0]["backend"] == "CUDA"
    assert "easiest" in rec[0]["reason"]
    names = [r["name"] for r in rec]
    assert "MLX" not in names                 # Apple-only never on NVIDIA
    assert "TensorRT-LLM" not in names        # safetensors-only
    vllm = [r for r in rec if r["name"] == "vLLM"]
    assert vllm and vllm[0]["tier"] == "alternative"
    assert "experimental" in vllm[0]["reason"]   # GGUF via plugin, honest note


def test_recommend_mac_safetensors():
    rec = servers.recommend_servers(SF_Q, "macbook")
    assert rec and rec[0]["name"] == "MLX" and rec[0]["backend"] == "Metal"
    assert rec[0]["reason"].startswith("Apple-native")
    names = [r["name"] for r in rec]
    assert "TensorRT-LLM" not in names
    assert "vLLM" not in names                # no official Apple path


def test_recommend_amd_consumer():
    rec = servers.recommend_servers(GGUF_Q, "amd")
    names = [r["name"] for r in rec]
    assert "Ollama" in names and "llama.cpp" in names
    assert "TGI" not in names and "SGLang" not in names   # Instinct-only
    assert "MLX" not in names


def test_recommend_intel_arc_and_snapdragon():
    arc = servers.recommend_servers(GGUF_Q, "intel_arc")
    assert arc and arc[0]["name"] == "Ollama" and arc[0]["backend"] == "Vulkan"
    sd = servers.recommend_servers(GGUF_Q, "snapdragon")
    assert sd and all(r["backend"].startswith("CPU") for r in sd)
    assert "vLLM" not in [r["name"] for r in sd]
