"""Generate the hand-written sample dataset (frontend-first, task 3.3).

Emits 8 schema-valid models (3B -> 671B, dense + MoE + GGUF) into models/
with index.json/index.js/bundle.js, then verifies:
  - schema validity of every record
  - the invariant recompute(quants[0]) == hardware{} (via estimator.hardware_flags)
Run: python make_samples.py   (idempotent)
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from whatllm import artifacts, estimator

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
TODAY = date.today().isoformat()


def _model(model_id: str, name: str, params_b: float, arch: str, pipeline_tag: str,
           trending_score: int, downloads: int, quants: list[dict]) -> dict:
    return {
        "id": model_id,
        "name": name,
        "author": model_id.split("/")[0],
        "parameters_b": params_b,
        "architecture": arch,
        "pipeline_tag": pipeline_tag,
        "hf_url": f"https://huggingface.co/{model_id}",
        "trending_score": trending_score,
        "downloads": downloads,
        "quants": quants,
        "hardware": estimator.hardware_flags(params_b, quants),
        "last_updated": TODAY,
    }


def build_samples() -> list[dict]:
    samples = []

    # 1. small dense, mobile-practical
    samples.append(_model(
        "microsoft/Phi-3-mini-4k-instruct", "Phi-3 Mini 4K Instruct", 3.82, "dense",
        "text-generation", 4120, 1_450_000, estimator.synthesize_quants(3.82)))

    # 2. mid dense (real params: 8.19B)
    samples.append(_model(
        "Qwen/Qwen3-8B", "Qwen3 8B", 8.19, "dense", "text-generation",
        3890, 3_200_000, estimator.synthesize_quants(8.19)))

    # 3. mid dense
    samples.append(_model(
        "meta-llama/Llama-3.1-8B-Instruct", "Llama 3.1 8B Instruct", 8.03, "dense",
        "text-generation", 2870, 9_800_000, estimator.synthesize_quants(8.03)))

    # 4. GGUF repo with REAL file sizes (bartowski measured values)
    gguf_quants = [
        {"name": "Q4_K_S", "size_gb": 4.69, "estimated_vram_gb": estimator.est_vram_gb(4.69), "notes": "Slightly lower quality with more space savings"},
        {"name": "Q4_K_M", "size_gb": 4.92, "estimated_vram_gb": estimator.est_vram_gb(4.92), "notes": "Recommended balanced quant"},
        {"name": "Q5_K_M", "size_gb": 5.73, "estimated_vram_gb": estimator.est_vram_gb(5.73), "notes": "Higher quality, slightly larger"},
        {"name": "Q6_K", "size_gb": 6.60, "estimated_vram_gb": estimator.est_vram_gb(6.60), "notes": "Very high quality"},
        {"name": "Q8_0", "size_gb": 8.54, "estimated_vram_gb": estimator.est_vram_gb(8.54), "notes": "Near-lossless, needs more VRAM"},
    ]
    samples.append(_model(
        "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF", "Llama 3.1 8B Instruct GGUF", 8.03,
        "dense", "text-generation", 1980, 278_000, gguf_quants))

    # 5. large dense
    samples.append(_model(
        "Qwen/Qwen2.5-14B-Instruct", "Qwen2.5 14B Instruct", 14.77, "dense",
        "text-generation", 1560, 5_100_000, estimator.synthesize_quants(14.77)))

    # 6. MoE (total params: 46.7B)
    samples.append(_model(
        "mistralai/Mixtral-8x7B-Instruct-v0.1", "Mixtral 8x7B Instruct", 46.7, "moe",
        "text-generation", 1120, 4_300_000, estimator.synthesize_quants(46.7)))

    # 7. huge dense
    samples.append(_model(
        "Qwen/Qwen2.5-72B-Instruct", "Qwen2.5 72B Instruct", 72.71, "dense",
        "text-generation", 940, 2_700_000, estimator.synthesize_quants(72.71)))

    # 8. extreme MoE (671B) -> Mac Studio 512 + DGX
    samples.append(_model(
        "deepseek-ai/DeepSeek-R1", "DeepSeek R1", 671.0, "moe", "text-generation",
        860, 6_500_000, estimator.synthesize_quants(671.0)))

    # 9. tiny dense -> phone-practical everywhere
    samples.append(_model(
        "meta-llama/Llama-3.2-1B", "Llama 3.2 1B", 1.23, "dense", "text-generation",
        640, 2_100_000, estimator.synthesize_quants(1.23)))

    # 10. small dense
    samples.append(_model(
        "Qwen/Qwen2.5-3B-Instruct", "Qwen2.5 3B Instruct", 3.09, "dense",
        "text-generation", 720, 1_800_000, estimator.synthesize_quants(3.09)))

    # 11. small dense
    samples.append(_model(
        "google/gemma-3-4b-it", "Gemma 3 4B IT", 3.8, "dense", "text-generation",
        590, 890_000, estimator.synthesize_quants(3.8)))

    # 12. mid-large dense
    samples.append(_model(
        "Qwen/Qwen3-32B", "Qwen3 32B", 32.76, "dense", "text-generation",
        830, 410_000, estimator.synthesize_quants(32.76)))

    # 13. huge dense (70B): MacBook 64+ per contract math
    samples.append(_model(
        "meta-llama/Llama-3.1-70B-Instruct", "Llama 3.1 70B Instruct", 70.6, "dense",
        "text-generation", 710, 1_500_000, estimator.synthesize_quants(70.6)))

    # 14. 304B MoE GGUF with REAL split-file quant sizes (unsloth UD quants, summed
    #     from the HF tree endpoint: UD-IQ1_M 86.9 GB ... UD-Q8_K_XL 161.9 GB)
    ds4_quants = [
        {"name": "UD-IQ1_M", "size_gb": 86.9, "estimated_vram_gb": estimator.est_vram_gb(86.9),
         "notes": "Aggressive 1-bit dynamic quant — only practical option for 128 GB Macs"},
        {"name": "UD-Q2_K_XL", "size_gb": 96.8, "estimated_vram_gb": estimator.est_vram_gb(96.8),
         "notes": "2-bit XL quant, compact"},
        {"name": "UD-Q3_K_XL", "size_gb": 128.2, "estimated_vram_gb": estimator.est_vram_gb(128.2),
         "notes": "3-bit XL quant"},
        {"name": "UD-Q4_K_XL", "size_gb": 155.1, "estimated_vram_gb": estimator.est_vram_gb(155.1),
         "notes": "4-bit XL quant — higher quality"},
        {"name": "UD-Q8_K_XL", "size_gb": 161.9, "estimated_vram_gb": estimator.est_vram_gb(161.9),
         "notes": "8-bit XL quant — highest quality"},
    ]
    samples.append(_model(
        "unsloth/DeepSeek-V4-Flash-0731-GGUF", "DeepSeek V4 Flash 0731 GGUF", 304.18,
        "moe", "text-generation", 625, 189_000, ds4_quants))

    return samples


def verify(models: list[dict]) -> None:
    errors = 0
    for m in models:
        errs = artifacts.validate_model(m)
        if errs:
            errors += 1
            print(f"  SCHEMA FAIL {m['id']}: {errs}")
        recomputed = estimator.hardware_flags(m["parameters_b"], m["quants"])
        if recomputed != m["hardware"]:
            errors += 1
            print(f"  INVARIANT FAIL {m['id']}: stored != recompute(quants[0])")
    print(f"verify: {len(models)} models, {errors} problems")


def main() -> None:
    samples = build_samples()
    artifacts.emit_artifacts(samples, MODELS_DIR)
    files = sorted(p.name for p in MODELS_DIR.glob("*.json"))
    print(f"wrote {len(samples)} model files into {MODELS_DIR}/")
    print("files:", ", ".join(files))
    verify(samples)


if __name__ == "__main__":
    main()
