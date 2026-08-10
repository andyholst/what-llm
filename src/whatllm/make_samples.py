"""Generate the hand-written sample dataset (frontend-first, task 3.3 / v3 metadata).

Emits 14 schema-v3-valid models (1B -> 671B, dense + MoE + GGUF) into models/
with index.json/index.js/bundle.js, then verifies:
  - schema validity of every record (incl. profile/license/context/model_type/...)
  - the invariant recompute(quants[0]) == hardware{} (via estimator.hardware_flags)
Run: python -m whatllm.make_samples   (idempotent)
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from whatllm import artifacts, estimator, profile, servers

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
TODAY = date.today().isoformat()


def _model(
    model_id: str,
    name: str,
    params_b: float,
    arch: str,
    pipeline_tag: str,
    trending_score: int,
    downloads: int,
    quants: list[dict],
    *,
    license_name: str = "unknown",
    commercial_ok: bool = True,
    context_window: int | None = 8192,
    model_type: str = "chat",
    languages: list[str] | None = None,
    knowledge_cutoff: str | None = None,
    benchmarks: list[dict] | None = None,
    tags: list[str] | None = None,
    gated: bool = False,
) -> dict:
    fam = profile.family_for(model_id)
    prof = profile.build_profile(
        model_id,
        family=fam,
        tags=tags,
        eval_entries=benchmarks,
        context_window=context_window,
        license_name=license_name,
        commercial_ok=commercial_ok,
        model_type=model_type,
        gated=gated,
    )
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
        "profile": prof,
        "license": license_name,
        "commercial_ok": commercial_ok,
        "context_window": context_window,
        "model_type": model_type,
        "languages": languages or [],
        "knowledge_cutoff": knowledge_cutoff,
        "benchmarks": benchmarks or [],
        "servers": servers.servers_for_model(quants),
        "last_updated": TODAY,
    }


def build_samples() -> list[dict]:
    samples = []

    # 1. small dense, mobile-practical
    samples.append(_model(
        "microsoft/Phi-3-mini-4k-instruct", "Phi-3 Mini 4K Instruct", 3.82, "dense",
        "text-generation", 4120, 1_450_000, estimator.synthesize_quants(3.82),
        license_name="mit", commercial_ok=True, context_window=4096,
        model_type="instruct", languages=["en"], knowledge_cutoff="2023-10",
        tags=["conversational"]))

    # 2. mid dense (real params: 8.19B)
    samples.append(_model(
        "Qwen/Qwen3-8B", "Qwen3 8B", 8.19, "dense", "text-generation",
        3890, 3_200_000, estimator.synthesize_quants(8.19),
        license_name="apache-2.0", commercial_ok=True, context_window=40960,
        model_type="chat", languages=["en", "zh"], knowledge_cutoff="2025-03",
        tags=["conversational", "text-generation-inference"]))

    # 3. mid dense
    samples.append(_model(
        "meta-llama/Llama-3.1-8B-Instruct", "Llama 3.1 8B Instruct", 8.03, "dense",
        "text-generation", 2870, 9_800_000, estimator.synthesize_quants(8.03),
        license_name="llama3.1", commercial_ok=True, context_window=131072,
        model_type="instruct", languages=["en", "de", "fr", "es", "hi", "pt", "zh"],
        knowledge_cutoff="2023-12", gated=True,
        tags=["conversational", "license:llama3.1"]))

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
        "dense", "text-generation", 1980, 278_000, gguf_quants,
        license_name="llama3.1", commercial_ok=True, context_window=131072,
        model_type="instruct", languages=["en", "de", "fr", "es", "hi", "pt", "zh"],
        knowledge_cutoff="2023-12", tags=["gguf"]))

    # 5. large dense
    samples.append(_model(
        "Qwen/Qwen2.5-14B-Instruct", "Qwen2.5 14B Instruct", 14.77, "dense",
        "text-generation", 1560, 5_100_000, estimator.synthesize_quants(14.77),
        license_name="qwen", commercial_ok=True, context_window=32768,
        model_type="instruct", languages=["en", "zh"], knowledge_cutoff="2024-09",
        tags=["conversational"]))

    # 6. MoE (total params: 46.7B)
    samples.append(_model(
        "mistralai/Mixtral-8x7B-Instruct-v0.1", "Mixtral 8x7B Instruct", 46.7, "moe",
        "text-generation", 1120, 4_300_000, estimator.synthesize_quants(46.7),
        license_name="apache-2.0", commercial_ok=True, context_window=32768,
        model_type="instruct", languages=["en", "fr", "de", "es", "it"],
        knowledge_cutoff="2023-12", tags=["conversational"]))

    # 7. huge dense
    samples.append(_model(
        "Qwen/Qwen2.5-72B-Instruct", "Qwen2.5 72B Instruct", 72.71, "dense",
        "text-generation", 940, 2_700_000, estimator.synthesize_quants(72.71),
        license_name="qwen", commercial_ok=True, context_window=131072,
        model_type="instruct", languages=["en", "zh"], knowledge_cutoff="2024-09",
        tags=["conversational"]))

    # 8. extreme MoE (671B) -> Mac Studio 512 + DGX
    samples.append(_model(
        "deepseek-ai/DeepSeek-R1", "DeepSeek R1", 671.0, "moe", "text-generation",
        860, 6_500_000, estimator.synthesize_quants(671.0),
        license_name="deepseek", commercial_ok=True, context_window=131072,
        model_type="reasoner", languages=["en", "zh"], knowledge_cutoff="2024-11",
        tags=["conversational", "reasoning"]))

    # 9. tiny dense -> phone-practical everywhere
    samples.append(_model(
        "meta-llama/Llama-3.2-1B", "Llama 3.2 1B", 1.23, "dense", "text-generation",
        640, 2_100_000, estimator.synthesize_quants(1.23),
        license_name="llama3.2", commercial_ok=True, context_window=131072,
        model_type="base", languages=["en", "de", "fr", "es", "hi", "pt", "zh"],
        knowledge_cutoff="2023-12", gated=True, tags=["license:llama3.2"]))

    # 10. small dense
    samples.append(_model(
        "Qwen/Qwen2.5-3B-Instruct", "Qwen2.5 3B Instruct", 3.09, "dense",
        "text-generation", 720, 1_800_000, estimator.synthesize_quants(3.09),
        license_name="qwen", commercial_ok=True, context_window=32768,
        model_type="instruct", languages=["en", "zh"], knowledge_cutoff="2024-09",
        tags=["conversational"]))

    # 11. small dense
    samples.append(_model(
        "google/gemma-3-4b-it", "Gemma 3 4B IT", 3.8, "dense", "text-generation",
        590, 890_000, estimator.synthesize_quants(3.8),
        license_name="gemma", commercial_ok=True, context_window=32768,
        model_type="instruct", languages=["en", "es", "de", "fr", "ja", "ko", "pt", "zh"],
        knowledge_cutoff="2025-02", gated=True, tags=["conversational"]))

    # 12. mid-large dense
    samples.append(_model(
        "Qwen/Qwen3-32B", "Qwen3 32B", 32.76, "dense", "text-generation",
        830, 410_000, estimator.synthesize_quants(32.76),
        license_name="apache-2.0", commercial_ok=True, context_window=131072,
        model_type="chat", languages=["en", "zh"], knowledge_cutoff="2025-03",
        tags=["conversational", "text-generation-inference"]))

    # 13. huge dense (70B): MacBook 64+ per contract math
    samples.append(_model(
        "meta-llama/Llama-3.1-70B-Instruct", "Llama 3.1 70B Instruct", 70.6, "dense",
        "text-generation", 710, 1_500_000, estimator.synthesize_quants(70.6),
        license_name="llama3.1", commercial_ok=True, context_window=131072,
        model_type="instruct", languages=["en", "de", "fr", "es", "hi", "pt", "zh"],
        knowledge_cutoff="2023-12", gated=True, tags=["conversational", "license:llama3.1"]))

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
        "moe", "text-generation", 625, 189_000, ds4_quants,
        license_name="deepseek", commercial_ok=True, context_window=131072,
        model_type="reasoner", languages=["en", "zh"], knowledge_cutoff="2025-07",
        tags=["gguf", "reasoning"]))

    # 15. non-commercial fine-tune (real-world: dolphin is CC-BY-NC) — the commercial
    #     filter must exclude it
    samples.append(_model(
        "cognitivecomputations/dolphin-2.9-llama-3.1-8b", "Dolphin 2.9 Llama 3.1 8B", 8.03,
        "dense", "text-generation", 540, 920_000, estimator.synthesize_quants(8.03),
        license_name="cc-by-nc-4.0", commercial_ok=False, context_window=131072,
        model_type="chat", languages=["en"], knowledge_cutoff="2023-12",
        tags=["conversational", "license:cc-by-nc-4.0"]))

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
        if not m["profile"]["provenance"]:
            errors += 1
            print(f"  PROFILE FAIL {m['id']}: empty provenance")
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
