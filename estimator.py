"""VRAM estimation + hardware compatibility mapping for the what-llm pipeline.

Pure functions, no I/O. Shared by crawl_models.py and make_samples.py.

Contract rules (openspec/changes/add-hf-model-pipeline/spec.md):
  - estimated_vram_gb = size_gb + OVERHEAD_GB   (KV-cache allowance, contract 4.9 -> 6.2)
  - a tier fits iff estimated_vram_gb + HEADROOM_GB <= tier_vram  (headroom applied ONCE)
  - MacBook usable memory = unified_memory - MAC_SYSTEM_GB
  - mobile practical iff params_b <= MOBILE_MAX_PARAMS_B and the smallest quant
    fits MOBILE_BUDGET_GB
  - MoE uses TOTAL parameters for size/VRAM (all experts resident in memory)
"""
from __future__ import annotations

# llama.cpp measured bits/weight (Llama-3.1-8B) / 8 -> bytes/param
BYTES_PER_PARAM = {
    "Q4_K_M": 0.612,  # 4.8944 bits/weight
    "Q5_K_M": 0.713,  # 5.7036
    "Q8_0": 1.063,    # 8.5008
    "FP16": 2.0,
}

OVERHEAD_GB = 1.3           # KV-cache allowance inside the estimate
HEADROOM_GB = 1.5           # fit-test margin on top of the estimate
MAC_SYSTEM_GB = 3.5         # unified memory reserved for macOS
MOBILE_BUDGET_GB = 8.0      # phone-class device budget
MOBILE_MAX_PARAMS_B = 4.0   # practical only for <=4B models

NVIDIA_TIERS = [8, 12, 16, 24, 48]
AMD_TIERS = [8, 12, 16, 24]
MACBOOK_TIERS = [16, 24, 32, 48]  # 48 displayed as "48+"

DEFAULT_NOTES = {
    "Q4_K_M": "Recommended balanced quant",
    "Q5_K_M": "Higher quality, slightly larger",
    "Q8_0": "Near-lossless, needs more VRAM",
    "FP16": "Full precision, most VRAM",
}

QUANT_FALLBACK_NOTES = {
    "Q2_K": "Very compact, low quality",
    "Q3_K_M": "Compact, low quality",
    "Q4_K_S": "Smaller 4-bit, good balance",
    "Q4_K_L": "Larger 4-bit, higher quality",
    "Q6_K": "Very high quality",
    "Q6_K_L": "Highest practical quality",
    "IQ2_M": "Experimental 2-bit, compact",
    "IQ3_M": "Experimental 3-bit",
    "IQ4_XS": "Experimental 4-bit, compact",
    "IQ4_NL": "Experimental 4-bit, near-lossless",
}

_MAC_KEYS = {"16": "16gb", "24": "24gb", "32": "32gb", "48": "48gb_plus"}


def quant_size_gb(params_b: float, bytes_per_param: float) -> float:
    """Weights-only size in GB for a quant of a model with `params_b` total params."""
    return round(params_b * bytes_per_param, 2)


def est_vram_gb(size_gb: float) -> float:
    """Estimated VRAM: weights + KV-cache allowance."""
    return round(size_gb + OVERHEAD_GB, 2)


def fits(est: float, tier_vram: float) -> bool:
    """Fit rule from the contract: est + 1.5 headroom <= tier VRAM."""
    return est + HEADROOM_GB <= tier_vram


def synthesize_quants(params_b: float) -> list[dict]:
    """Default quant list for a model without real GGUF files (total params for MoE)."""
    names = ["Q4_K_M", "Q5_K_M", "Q8_0"]
    if params_b <= 9.0:
        names.append("FP16")
    quants = []
    for name in names:
        size = quant_size_gb(params_b, BYTES_PER_PARAM[name])
        quants.append({
            "name": name,
            "size_gb": size,
            "estimated_vram_gb": est_vram_gb(size),
            "notes": DEFAULT_NOTES[name],
        })
    return quants


def quant_from_file(name: str, size_bytes: int) -> dict:
    """Quant entry from a real GGUF file size (decimal GB, matching HF's display)."""
    size_gb = round(size_bytes / 1e9, 2)
    return {
        "name": name,
        "size_gb": size_gb,
        "estimated_vram_gb": est_vram_gb(size_gb),
        "notes": DEFAULT_NOTES.get(name, QUANT_FALLBACK_NOTES.get(name, "GGUF quant")),
    }


def _tier_flags(est: float, tiers: list[int]) -> dict[str, bool]:
    return {f"{t}gb": fits(est, t) for t in tiers}


def _mac_flags(est: float) -> dict[str, bool]:
    return {_MAC_KEYS[str(t)]: fits(est, t - MAC_SYSTEM_GB) for t in MACBOOK_TIERS}


def hardware_flags(params_b: float, quants: list[dict]) -> dict:
    """Hardware compatibility anchored on the recommended quant (quants[0])."""
    if not quants:
        raise ValueError("hardware_flags requires at least one quant")
    est = quants[0]["estimated_vram_gb"]
    min_est = min(q["estimated_vram_gb"] for q in quants)

    nvidia = _tier_flags(est, NVIDIA_TIERS)
    amd = _tier_flags(est, AMD_TIERS)
    macbook = _mac_flags(est)

    mobile_practical = params_b <= MOBILE_MAX_PARAMS_B and fits(min_est, MOBILE_BUDGET_GB)
    if mobile_practical:
        min_q = min(quants, key=lambda q: q["estimated_vram_gb"])
        mobile_note = (
            f"Practical at {min_q['name']} (~{min_q['estimated_vram_gb']} GB est.)"
            " on phone-class hardware"
        )
    elif params_b > MOBILE_MAX_PARAMS_B:
        mobile_note = "Too large for phones"
    else:
        mobile_note = f"Smallest quant exceeds an {MOBILE_BUDGET_GB:.0f} GB mobile budget"

    any_consumer = any(nvidia.values()) or any(macbook.values())
    if not any_consumer:
        mobile_note = "No consumer hardware fits; multi-GPU/server only"

    return {
        "nvidia": nvidia,
        "amd": amd,
        "macbook": macbook,
        "mobile": {"practical": mobile_practical, "note": mobile_note},
    }
