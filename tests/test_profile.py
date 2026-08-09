"""Hermetic tests for the Python-derived model profile module (tasks 2.1-2.4).

No network: READMEs are fixtures; structured inputs are dicts.
"""
from __future__ import annotations

from whatllm import profile

QWEN_README = """# Qwen3-8B
## Model Overview
Qwen3 is a strong general-purpose chat model.
## Highlights
- Excellent multilingual chat quality
- Fast inference on consumer GPUs
## Limitations
- Knowledge cutoff at training time
- May produce hallucinations on niche topics
## Intended use
- coding assistant
- document summarization
"""

GATED_MODEL = None  # no README when gated


def test_mine_limitations_section():
    mined = profile.split_sections(QWEN_README)
    assert mined["limitations"] == [
        "Knowledge cutoff at training time",
        "May produce hallucinations on niche topics",
    ]


def test_mine_strengths_and_use_cases():
    mined = profile.split_sections(QWEN_README)
    assert mined["strengths"] == [
        "Excellent multilingual chat quality",
        "Fast inference on consumer GPUs",
    ]
    assert "intended_use" in mined


def test_infer_use_cases_keywords():
    found = profile.infer_use_cases("Great for coding and summarization tasks", ["conversational"])
    assert "coding" in found and "summarization" in found and "chat" in found


def test_family_for():
    assert profile.family_for("Qwen/Qwen3-8B") == "qwen"
    assert profile.family_for("bartowski/Meta-Llama-3.1-8B-Instruct-GGUF") == "bartowski"
    assert profile.family_for("unknown-org/whatever") is None


def test_evals_become_strength_with_provenance():
    p = profile.build_profile("Qwen/Qwen3-8B", eval_entries=[
        {"dataset": "LiquidAI/ifstruct-v1.0", "value": 79.75, "verified": False},
    ])
    assert any("ifstruct" in s and "unverified" in s for s in p["strengths"])
    assert any(pv["source"] == "evals" for pv in p["provenance"])


def test_context_capability_and_short_limit():
    p = profile.build_profile("Qwen/Qwen3-8B", context_window=40960)
    assert any("40,960" in s for s in p["strengths"])
    p2 = profile.build_profile("old/model", context_window=2048)
    assert any("Short context window" in l for l in p2["limitations"])


def test_non_commercial_license_limitation():
    p = profile.build_profile("x/y", license_name="cc-by-nc-4.0", commercial_ok=False)
    assert any("Non-commercial license" in l for l in p["limitations"])
    assert any(pv["source"] == "tags" for pv in p["provenance"])


def test_gated_model_uses_curated_fallback():
    p = profile.build_profile("Qwen/Qwen3-8B", family="qwen", gated=True)
    assert any(l == "Model card is gated — README not accessible to anonymous crawls"
               for l in p["limitations"])
    assert any(s == "Strong instruction following and general chat" for s in p["strengths"])
    sources = {pv["source"] for pv in p["provenance"]}
    assert "curated" in sources and "config" in sources


def test_base_model_limitation():
    p = profile.build_profile("meta-llama/Llama-3.2-1B", family="llama", model_type="base")
    assert any("Base (pre-instruct)" in l for l in p["limitations"])


def test_best_for_curated_plus_readme_keywords():
    p = profile.build_profile("Qwen/Qwen3-8B", family="qwen", readme_text=QWEN_README)
    for uc in ("chat", "reasoning", "coding", "summarization", "rag"):
        assert uc in p["best_for"], f"missing {uc} in {p['best_for']}"


def test_every_claim_has_provenance():
    p = profile.build_profile("Qwen/Qwen3-8B", family="qwen", readme_text=QWEN_README,
                              context_window=40960, eval_entries=[{"dataset": "d", "value": 1.0, "verified": False}])
    n_claims = len(p["strengths"]) + len(p["weaknesses"]) + len(p["limitations"])
    assert len(p["provenance"]) == n_claims
    for pv in p["provenance"]:
        assert pv["source"] in ("readme", "evals", "config", "tags", "curated")
