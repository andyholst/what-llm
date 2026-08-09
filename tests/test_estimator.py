"""Estimator unit tests — VRAM math and hardware flag mapping (tasks 2.3-2.5).

Skeptic-verified values: bytes/param from llama.cpp measured bits (Q4_K_M 0.612,
Q5_K_M 0.713, Q8_0 1.063, FP16 2.0); real GGUF file sizes from the tree endpoint
(bartowski Q4_K_M = 4,920,739,232 bytes = 4.92 GB decimal).
"""
from __future__ import annotations

from whatllm import estimator


# ---- bytes/param table (task 2.3) ----
def test_bytes_per_param_table():
    assert estimator.BYTES_PER_PARAM["Q4_K_M"] == 0.612
    assert estimator.BYTES_PER_PARAM["Q5_K_M"] == 0.713
    assert estimator.BYTES_PER_PARAM["Q8_0"] == 1.063
    assert estimator.BYTES_PER_PARAM["FP16"] == 2.0


def test_quant_size_gb_8b_q4():
    # Llama-3.1-8B: 8.03e9 x 0.612 = 4.914 -> 4.91 GB (matches real 4.92 GB file)
    assert estimator.quant_size_gb(8.03, estimator.BYTES_PER_PARAM["Q4_K_M"]) == 4.91


def test_est_vram_gb_contract_example():
    # contract example: size 4.9 -> est 6.2 (overhead 1.3)
    assert estimator.est_vram_gb(4.9) == 6.2


def test_fits_rule_8gb_tier():
    # contract: fit iff est + 1.5 <= tier. 8B Q4_K_M: 6.21 + 1.5 = 7.71 <= 8
    assert estimator.fits(6.21, 8) is True
    assert estimator.fits(6.5, 8) is True   # boundary: 6.5 + 1.5 = 8.0 exactly
    assert estimator.fits(6.51, 8) is False


def test_quant_from_file_decimal_gb():
    # bartowski Q4_K_M real size: 4,920,739,232 bytes = 4.92 GB (decimal)
    q = estimator.quant_from_file("Q4_K_M", 4_920_739_232)
    assert q["size_gb"] == 4.92
    assert q["estimated_vram_gb"] == 6.22
    assert q["notes"]


# ---- quant synthesis (task 2.3) ----
def test_synthesize_quants_small_includes_fp16():
    qs = estimator.synthesize_quants(3.82)
    names = [q["name"] for q in qs]
    assert names == ["Q4_K_M", "Q5_K_M", "Q8_0", "FP16"]
    assert qs[0]["size_gb"] == round(3.82 * 0.612, 2)


def test_synthesize_quants_large_no_fp16():
    qs = estimator.synthesize_quants(46.7)
    names = [q["name"] for q in qs]
    assert names == ["Q4_K_M", "Q5_K_M", "Q8_0"]
    # MoE uses TOTAL params: 46.7 x 0.612 = 28.58 GB
    assert qs[0]["size_gb"] == 28.58
    assert qs[0]["estimated_vram_gb"] == 29.88


# ---- hardware flags (task 2.4) ----
def test_flags_8b_fits_8gb():
    qs = estimator.synthesize_quants(8.03)
    hw = estimator.hardware_flags(8.03, qs)
    assert hw["nvidia"]["8gb"] is True
    assert hw["nvidia"]["48gb"] is True
    assert hw["amd"]["8gb"] is True
    assert hw["macbook"]["16gb"] is True    # usable 12.5; 6.21+1.5=7.71 <= 12.5
    assert hw["macbook"]["48gb_plus"] is True
    assert hw["mobile"]["practical"] is False  # 8.03B > 4B


def test_flags_70b_only_48gb():
    qs = estimator.synthesize_quants(72.71)
    hw = estimator.hardware_flags(72.71, qs)
    assert hw["nvidia"] == {"8gb": False, "12gb": False, "16gb": False,
                            "24gb": False, "48gb": True}
    assert hw["amd"] == {"8gb": False, "12gb": False, "16gb": False, "24gb": False}
    # est = 44.5 + 1.3 = 45.8; fit: 45.8 + 1.5 = 47.3
    # MacBook usable = tier - 3.5: 48 - 3.5 = 44.5 -> 47.3 > 44.5, so even 48+ misses
    assert hw["macbook"]["48gb_plus"] is False
    assert hw["macbook"]["32gb"] is False


def test_flags_mixtral_moe_contract_math():
    # 46.7B total x 0.612 = 28.58 -> est 29.88; fit: 29.88+1.5=31.38
    # 32GB MacBook usable = 28.5 -> 31.38 > 28.5: does NOT fit 32GB
    # 48GB MacBook usable = 44.5 -> fits
    qs = estimator.synthesize_quants(46.7)
    hw = estimator.hardware_flags(46.7, qs)
    assert hw["nvidia"]["24gb"] is False
    assert hw["nvidia"]["48gb"] is True
    assert hw["macbook"]["32gb"] is False
    assert hw["macbook"]["48gb_plus"] is True
    assert hw["mobile"]["practical"] is False


def test_flags_extreme_moe_no_consumer_support():
    qs = estimator.synthesize_quants(671.0)  # DeepSeek-R1 class
    hw = estimator.hardware_flags(671.0, qs)
    assert all(not v for v in hw["nvidia"].values())
    assert all(not v for v in hw["amd"].values())
    assert all(not v for v in hw["macbook"].values())
    assert hw["mobile"]["practical"] is False
    assert "multi-GPU" in hw["mobile"]["note"]


def test_flags_mobile_practical_for_small():
    qs = estimator.synthesize_quants(3.82)
    hw = estimator.hardware_flags(3.82, qs)
    assert hw["mobile"]["practical"] is True
    assert "phone-class" in hw["mobile"]["note"]


def test_flags_anchored_on_first_quant():
    # hardware{} MUST equal recompute(quants[0]) — the frontend invariant
    qs = estimator.synthesize_quants(8.19)
    hw = estimator.hardware_flags(8.19, qs)
    est0 = qs[0]["estimated_vram_gb"]
    assert hw["nvidia"]["8gb"] == estimator.fits(est0, 8)
    assert hw["macbook"]["16gb"] == estimator.fits(est0, 16 - estimator.MAC_SYSTEM_GB)


def test_hardware_flags_requires_quants():
    try:
        estimator.hardware_flags(8.0, [])
    except ValueError:
        return
    raise AssertionError("expected ValueError for empty quants")
