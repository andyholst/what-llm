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
        "nvidia": {"8gb": True, "12gb": True, "16gb": True, "24gb": True, "48gb": True},
        "amd": {"8gb": True, "12gb": True, "16gb": True, "24gb": True},
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
}


def validate(record) -> list[str]:
    v = Draft7Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    return [e.message for e in v.iter_errors(record)]


def test_valid_record_passes():
    assert validate(VALID) == []


@pytest.mark.parametrize("field", [
    "id", "name", "author", "parameters_b", "architecture", "pipeline_tag",
    "hf_url", "trending_score", "downloads", "quants", "hardware", "last_updated",
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


def test_date_pattern():
    rec = dict(VALID, last_updated="09/08/2026")
    assert validate(rec)


def test_parameters_must_be_positive():
    rec = dict(VALID, parameters_b=0)
    assert validate(rec)
