"""Hermetic tests for the inference-server catalog (inference-server-catalog 1.x)."""
from __future__ import annotations

from whatllm import servers


def test_catalog_completeness():
    names = {s["name"] for s in servers.SERVERS}
    assert {"llama.cpp", "Ollama", "vLLM", "LM Studio", "koboldcpp", "TGI"} <= names
    for s in servers.SERVERS:
        assert s["url"].startswith("http")
        assert s["format"] in ("gguf", "safetensors")
        assert "nvidia" in s["backends"] and "snapdragon" in s["backends"]


def test_backend_matrix_sanity():
    by = {s["name"]: s for s in servers.SERVERS}
    assert by["vLLM"]["backends"]["snapdragon"] is None      # no Vulkan path
    assert by["vLLM"]["backends"]["macbook"] is None
    assert by["Ollama"]["backends"]["nvidia"] == "CUDA"
    assert by["llama.cpp"]["backends"]["intel_arc"] == "SYCL/Vulkan"
    assert by["llama.cpp"]["backends"]["snapdragon"] == "CPU/Vulkan"


def test_gguf_quants_yield_gguf_servers():
    quants = [
        {"name": "Q4_K_M", "size_gb": 4.9, "estimated_vram_gb": 6.2, "notes": ""},
        {"name": "UD-IQ1_M", "size_gb": 86.9, "estimated_vram_gb": 88.2, "notes": ""},
    ]
    got = servers.servers_for_model(quants)
    assert "llama.cpp" in got and "Ollama" in got and "LM Studio" in got
    assert "koboldcpp" in got and "vLLM" not in got and "TGI" not in got


def test_safetensors_quants_yield_vllm():
    quants = [{"name": "full_precision", "size_gb": 16.0, "estimated_vram_gb": 17.3, "notes": ""}]
    got = servers.servers_for_model(quants)
    assert "vLLM" in got and "TGI" in got and "llama.cpp" not in got


def test_empty_quants_yield_empty():
    assert servers.servers_for_model([]) == []
