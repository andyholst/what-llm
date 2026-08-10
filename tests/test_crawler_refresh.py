"""Hermetic tests for the refresh crawler (refresh-crawler change).

`python -m whatllm.crawl_models --refresh --out <dir>` re-fetches EXISTING model
files and updates volatile metadata (downloads, trending_score, license, context,
profile) while preserving quants + hardware flags. All HTTP is mocked.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import whatllm.crawl_models as cm

OLD_DOWNLOADS = 12345
NEW_DOWNLOADS = 99999
NEW_TRENDING = 777.5


def _seed_record(path: Path) -> dict:
    def flags(keys):
        return {k: True for k in keys}

    rec = {
        "id": "Qwen/Qwen3-8B",
        "name": "Qwen3-8B",
        "author": "Qwen",
        "parameters_b": 8.19,
        "architecture": "dense",
        "pipeline_tag": "text-generation",
        "hf_url": "https://huggingface.co/Qwen/Qwen3-8B",
        "trending_score": 10.0,
        "downloads": OLD_DOWNLOADS,
        "license": "apache-2.0",
        "commercial_ok": True,
        "context_window": 40960,
        "model_type": "instruct",
        "languages": ["en", "zh"],
        "knowledge_cutoff": "2025-05",
        "benchmarks": [],
        "servers": ["llama.cpp", "Ollama", "LM Studio", "koboldcpp"],
        "quants": [{"name": "Q4_K_M", "size_gb": 4.9, "estimated_vram_gb": 6.2, "notes": ""}],
        "hardware": {
            "nvidia": flags(["8gb", "12gb", "16gb", "20gb", "24gb", "32gb", "48gb", "96gb"]),
            "amd": flags(["8gb", "12gb", "16gb", "20gb", "24gb", "32gb", "48gb", "192gb"]),
            "intel_arc": flags(["8gb", "10gb", "12gb", "16gb"]),
            "snapdragon": flags(["16gb", "32gb", "64gb"]),
            "macbook": flags(["16gb", "24gb", "36gb", "48gb", "64gb", "128gb"]),
            "mac_studio": flags(["36gb", "64gb", "96gb", "128gb", "192gb", "384gb", "512gb"]),
            "dgx": flags(["640gb", "1128gb", "1440gb"]),
            "android": {**flags(["8gb", "12gb", "16gb", "24gb"]), "note": "n/a"},
            "iphone": {**flags(["8gb", "12gb"]), "note": "n/a"},
        },
        "profile": {"summary": "seed", "best_for": ["chat"], "strengths": [],
                    "weaknesses": [], "limitations": [], "provenance": []},
        "last_updated": "2026-08-01",
    }
    path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return rec


def _detail() -> dict:
    return {
        "id": "Qwen/Qwen3-8B", "name": "Qwen3-8B", "author": "Qwen",
        "downloads": NEW_DOWNLOADS, "trendingScore": NEW_TRENDING,
        "gated": False, "pipeline_tag": "text-generation",
        "tags": ["text-generation", "license:apache-2.0", "en", "zh"],
        "cardData": {"license": "apache-2.0", "base_model": ["Qwen/Qwen3-8B"]},
        "evalResults": [],
        "config": {"model_type": "qwen3"},
    }


def _fake_http(monkeypatch, tmp_path: Path):
    detail = _detail()
    calls = {"n": 0}

    def f_json(url, params=None, **kw):
        if "/models/Qwen/Qwen3-8B" in url and params:
            calls["n"] += 1
            return detail, None
        if url.endswith("/raw/main/config.json"):
            return {"max_position_embeddings": 40960, "model_type": "qwen3"}, None
        raise AssertionError(f"unexpected detail url: {url}")

    def f_text(url, **kw):
        return "# Qwen3-8B\nIntended uses: chat, reasoning, coding\n## Limitations\nBeta."

    monkeypatch.setattr(cm, "http_get_json", f_json)
    monkeypatch.setattr(cm, "http_get_text", f_text)
    return calls


def test_refresh_updates_volatile_fields_preserves_quants(monkeypatch, tmp_path):
    seed = _seed_record(tmp_path / "Qwen__Qwen3-8B.json")
    _fake_http(monkeypatch, tmp_path)
    crawler = cm.Crawler(out_dir=str(tmp_path), dry_run=False)
    crawler.refresh(in_dir=str(tmp_path))
    crawler.emit()   # main() emits after refresh — mirror the CLI flow
    assert len(crawler.models) == 1
    rec = crawler.models[0]
    assert rec["downloads"] == NEW_DOWNLOADS
    assert rec["trending_score"] == NEW_TRENDING
    assert rec["last_updated"] == date.today().isoformat()
    # quants + hardware flags preserved (refresh never re-derives them)
    assert rec["quants"] == seed["quants"]
    assert rec["hardware"] == seed["hardware"]
    # enrichment re-ran: profile rebuilt from README signals
    assert rec["profile"]["summary"] != "seed"
    # schema-valid + artifacts emitted
    assert artifacts_schema_valid(rec)
    assert (tmp_path / "index.json").exists()


def artifacts_schema_valid(rec) -> bool:
    import whatllm.artifacts as artifacts
    return not artifacts.validate_model(rec)


def test_refresh_missing_dir_raises(tmp_path):
    import pytest
    crawler = cm.Crawler(out_dir=str(tmp_path / "nope"), dry_run=False)
    with pytest.raises(cm.HFError):
        crawler.refresh(in_dir=str(tmp_path / "nope"))


def test_refresh_skips_artifacts_and_bad_files(monkeypatch, tmp_path):
    (tmp_path / "index.json").write_text("{}", encoding="utf-8")
    _seed_record(tmp_path / "Qwen__Qwen3-8B.json")
    _fake_http(monkeypatch, tmp_path)
    crawler = cm.Crawler(out_dir=str(tmp_path), dry_run=False)
    crawler.refresh(in_dir=str(tmp_path))
    assert len(crawler.models) == 1  # only the model file, index.json skipped


def test_parser_exposes_refresh_flags():
    p = cm.build_parser()
    args = p.parse_args(["--refresh", "--out", "/tmp/x", "--in", "/tmp/y"])
    assert args.refresh is True
    assert args.out == "/tmp/x"
    assert args.in_dir == "/tmp/y"
    args2 = p.parse_args([])
    assert args2.refresh is False
