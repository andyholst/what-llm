"""Schema conformance tests for schemas/model.schema.json (task 2.2).

Loads the schema directly (no import from artifacts.py — that module ships in PR-3).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "model.schema.json"

VALID = {
    "id": "Qwen/Qwen3-8B",
    "name": "Qwen3 8B",
    "author": "Qwen",
    "parameters_b": 8.19,
    "architecture": "dense",
    "pipeline_tag": "text-generation",
    "hf_url": "https://huggingface.co/Qwen/Qwen3-8B",
    "trending_score": 3890,
    "downloads": 3200000,
    "quants": [
        {"name": "Q4_K_M", "size_gb": 4.91, "estimated_vram_gb": 6.21,
         "notes": "Recommended balanced quant"},
    ],
    "hardware": {
        "nvidia": {"8gb": True, "12gb": True, "16gb": True, "20gb": True, "24gb": True,
                   "32gb": True, "48gb": True, "96gb": True},
        "amd": {"8gb": True, "12gb": True, "16gb": True, "20gb": True, "24gb": True,
                "32gb": True, "48gb": True, "192gb": True},
        "intel_arc": {"8gb": True, "10gb": True, "12gb": True, "16gb": True},
        "snapdragon": {"16gb": True, "32gb": True, "64gb": True},
        "macbook": {"16gb": True, "24gb": True, "32gb": True, "48gb": True,
                    "64gb": True, "96gb": True, "128gb": True},
        "mac_studio": {"32gb": True, "64gb": True, "96gb": True, "128gb": True,
                       "192gb": True, "256gb": True, "512gb": True},
        "dgx": {"640gb": True, "1128gb": True, "1440gb": True},
        "android": {"8gb": True, "12gb": True, "16gb": True, "24gb": True,
                    "note": "Practical at the smallest quant (~3.6 GB est.) on flagship Android"},
        "iphone": {"8gb": True, "12gb": True,
                   "note": "Practical at the smallest quant (~3.6 GB est.) on flagship iPhone"},
    },
    "last_updated": "2026-08-09",
    "profile": {
        "summary": "Qwen: strong general-purpose chat.",
        "best_for": ["chat", "reasoning"],
        "strengths": ["Strong instruction following"],
        "weaknesses": ["Heavier than comparable models"],
        "limitations": ["Knowledge cutoff at training time"],
        "provenance": [{"claim": "Strong instruction following", "source": "curated", "confidence": "medium"}],
    },
    "license": "apache-2.0",
    "commercial_ok": True,
    "context_window": 40960,
    "model_type": "chat",
    "languages": ["en", "zh"],
    "knowledge_cutoff": "2025-03",
    "benchmarks": [{"dataset": "ifstruct-v1.0", "value": 79.75, "verified": False, "date": "2026-06-30", "source": "community"}],
}


def validate(record) -> list[str]:
    v = Draft7Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    return [e.message for e in v.iter_errors(record)]


def test_valid_record_passes():
    assert validate(VALID) == []


@pytest.mark.parametrize("field", [
    "id", "name", "author", "parameters_b", "architecture", "pipeline_tag",
    "hf_url", "trending_score", "downloads", "quants", "hardware", "last_updated",
    "profile", "license", "commercial_ok", "context_window", "model_type",
    "languages", "knowledge_cutoff", "benchmarks",
])
def test_missing_required_field_fails(field):
    rec = {k: v for k, v in VALID.items() if k != field}
    assert validate(rec), f"expected failure when {field!r} is missing"


def test_extra_field_rejected():
    rec = dict(VALID, extra_stuff="nope")
    assert validate(rec)


def test_architecture_enum():
    for bad in ("mixture", "DENSE", 1):
        rec = dict(VALID, architecture=bad)
        assert validate(rec), f"expected failure for architecture={bad!r}"


def test_hf_url_pattern():
    rec = dict(VALID, hf_url="http://example.com/not-hf")
    assert validate(rec)


def test_quant_missing_notes():
    rec = json.loads(json.dumps(VALID))
    del rec["quants"][0]["notes"]
    assert validate(rec)


def test_quant_empty_list():
    rec = dict(VALID, quants=[])
    assert validate(rec)


def test_hardware_missing_android_note():
    rec = json.loads(json.dumps(VALID))
    del rec["hardware"]["android"]["note"]
    assert validate(rec)


def test_mobile_category_rejected():
    rec = json.loads(json.dumps(VALID))
    rec["hardware"]["mobile"] = {"practical": False, "note": "legacy"}
    assert validate(rec)  # additionalProperties: false on hardware


def test_macbook_48gb_plus_key_rejected():
    rec = json.loads(json.dumps(VALID))
    rec["hardware"]["macbook"] = {k: True for k in ("16gb", "24gb", "32gb", "48gb_plus")}
    assert validate(rec)


def test_bad_model_type_rejected():
    rec = json.loads(json.dumps(VALID))
    rec["model_type"] = "hybrid"
    assert validate(rec)


def test_benchmark_requires_verified():
    rec = json.loads(json.dumps(VALID))
    del rec["benchmarks"][0]["verified"]
    assert validate(rec)


def test_profile_provenance_source_enum():
    rec = json.loads(json.dumps(VALID))
    rec["profile"]["provenance"][0]["source"] = "hunches"
    assert validate(rec)


def test_profile_requires_all_slots():
    rec = json.loads(json.dumps(VALID))
    del rec["profile"]["limitations"]
    assert validate(rec)


def test_date_pattern():
    rec = dict(VALID, last_updated="09/08/2026")
    assert validate(rec)


def test_parameters_must_be_positive():
    rec = dict(VALID, parameters_b=0)
    assert validate(rec)

def test_snapdragon_requires_all_unified_tiers():
    rec = json.loads(json.dumps(VALID))
    rec["hardware"]["snapdragon"] = {"16gb": True, "32gb": True}  # missing 64gb
    assert validate(rec)


def test_intel_arc_rejects_unknown_tier():
    rec = json.loads(json.dumps(VALID))
    rec["hardware"]["intel_arc"]["9gb"] = True  # no 9 GB Arc card exists
    assert validate(rec)


def test_nvidia_32gb_tier_valid():
    rec = json.loads(json.dumps(VALID))
    rec["hardware"]["nvidia"]["32gb"] = True   # RTX 5090 tier key
    assert validate(rec) == []
