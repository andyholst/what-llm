"""Hermetic tests for crawler metadata enrichment (extend-model-metadata 3.1-3.3).

Covers license/commercial_ok, context_window (raw config.json), model_type taxonomy,
languages, knowledge_cutoff, benchmarks mapping, gated-model skipping, and profile
assembly through Crawler._enrich and a full run() integration.
"""
from __future__ import annotations

import json

import pytest

import test_crawler as tc
import whatllm.crawl_models as cm


@pytest.fixture
def fake(monkeypatch):
    f = tc.FakeAPI()
    monkeypatch.setattr(cm, "http_get_json", f)
    monkeypatch.setattr(
        cm, "http_get_text",
        lambda url: f.readmes.get(url.split("huggingface.co/")[1].split("/raw/main")[0]))
    return f


def enriched_detail(model_id="Qwen/Qwen3-8B", **over):
    d = tc.raw_entry(model_id)
    d.update({
        "gated": False,
        "tags": ["conversational", "license:apache-2.0", "en", "zh"],
        "cardData": {"license": "apache-2.0", "base_model": ["Qwen/Qwen3-8B-Base"]},
        "evalResults": [{
            "filename": ".eval_results/x.yaml", "verified": False,
            "data": {"dataset": {"id": "ifstruct-v1.0"}, "value": 79.75,
                     "date": "2026-06-30", "source": {"name": "community"}},
            "pullRequest": 39,
        }],
    })
    d.update(over)
    return d


def test_license_and_commercial_ok_from_carddata(fake):
    rec = cm.Crawler.extract(enriched_detail())
    cm.Crawler._enrich(rec, enriched_detail(), None, None)
    assert rec["license"] == "apache-2.0"
    assert rec["commercial_ok"] is True


def test_nc_license_sets_commercial_ok_false(fake):
    detail = enriched_detail(cardData={"license": "cc-by-nc-4.0"})
    rec = cm.Crawler.extract(detail)
    cm.Crawler._enrich(rec, detail, None, None)
    assert rec["commercial_ok"] is False
    assert any("Non-commercial license" in l for l in rec["profile"]["limitations"])


def test_license_tag_fallback_when_carddata_absent(fake):
    detail = enriched_detail(cardData={}, tags=["license:llama3.1", "conversational"])
    rec = cm.Crawler.extract(detail)
    cm.Crawler._enrich(rec, detail, None, None)
    assert rec["license"] == "llama3.1"
    assert rec["commercial_ok"] is True  # conditional, not in NC denylist


def test_context_window_from_raw_config(fake):
    fake.configs["Qwen/Qwen3-8B"] = {"max_position_embeddings": 40960}
    rec = cm.Crawler.extract(enriched_detail())
    cm.Crawler._enrich(rec, enriched_detail(), None, fake.configs["Qwen/Qwen3-8B"])
    assert rec["context_window"] == 40960
    assert any("40,960" in s for s in rec["profile"]["strengths"])


def test_context_window_n_positions_fallback(fake):
    rec = cm.Crawler.extract(enriched_detail())
    cm.Crawler._enrich(rec, enriched_detail(), None, {"n_positions": 1024})
    assert rec["context_window"] == 1024


def test_model_type_instruct_via_base_model_list(fake):
    rec = cm.Crawler.extract(enriched_detail())
    cm.Crawler._enrich(rec, enriched_detail(), None, None)
    assert rec["model_type"] in ("chat", "instruct")  # conversational tag -> chat


def test_model_type_base_when_no_base_model(fake):
    detail = enriched_detail(cardData={}, tags=["en"])
    rec = cm.Crawler.extract(detail)
    cm.Crawler._enrich(rec, detail, None, None)
    assert rec["model_type"] == "base"
    assert any("Base (pre-instruct)" in l for l in rec["profile"]["limitations"])


def test_model_type_reasoner_and_vision(fake):
    r = cm.Crawler.extract(enriched_detail("DeepSeek/DeepSeek-R1", gated=False, tags=[]))
    cm.Crawler._enrich(r, enriched_detail("DeepSeek/DeepSeek-R1", gated=False, tags=[]), None, None)
    assert r["model_type"] == "reasoner"
    v = cm.Crawler.extract(enriched_detail("Qwen/Qwen2.5-VL-7B", gated=False, tags=[]))
    cm.Crawler._enrich(v, enriched_detail("Qwen/Qwen2.5-VL-7B", gated=False, tags=[]), None, None)
    assert v["model_type"] == "vision"


def test_languages_iso_filter(fake):
    rec = cm.Crawler.extract(enriched_detail())
    cm.Crawler._enrich(rec, enriched_detail(), None, None)
    assert rec["languages"] == ["en", "zh"]


def test_knowledge_cutoff_from_readme(fake):
    readme = "# M\n## Model Overview\nKnowledge cutoff: 2025-03-15\n"
    rec = cm.Crawler.extract(enriched_detail())
    cm.Crawler._enrich(rec, enriched_detail(), readme, None)
    assert rec["knowledge_cutoff"] == "2025-03"


def test_benchmarks_mapped_from_evalresults(fake):
    rec = cm.Crawler.extract(enriched_detail())
    cm.Crawler._enrich(rec, enriched_detail(), None, None)
    assert rec["benchmarks"] == [{
        "dataset": "ifstruct-v1.0", "value": 79.75, "verified": False,
        "date": "2026-06-30", "source": "community",
    }]


def test_gated_model_skips_readme_and_config(fake, tmp_path):
    detail = enriched_detail("meta-llama/Llama-3.1-8B-Instruct", gated="manual")
    c = tc.make_crawler(fake, limit=2, focus="none", state_file=str(tmp_path / "s.json"))
    fake.pages = [[detail]]
    fake.details["meta-llama/Llama-3.1-8B-Instruct"] = detail
    models = c.run()
    raw_urls = [u for u, _ in fake.calls if "/raw/main/" in u]
    assert raw_urls == []
    assert models[0]["profile"]["limitations"], "gated limitation expected"
    assert any("gated" in l.lower() for l in models[0]["profile"]["limitations"])


def test_run_emits_v3_schema_valid_records(fake, tmp_path):
    c = tc.make_crawler(fake, limit=2, focus="none", out_dir="models",
                        state_file=str(tmp_path / "s.json"))
    fake.pages = [[tc.raw_entry("a/m1")]]
    fake.details["a/m1"] = tc.raw_entry("a/m1")
    models = c.run()
    assert len(models) == 1
    m = models[0]
    from whatllm import artifacts
    assert artifacts.validate_model(m) == []
    for field in ("profile", "license", "commercial_ok", "context_window",
                  "model_type", "languages", "knowledge_cutoff", "benchmarks"):
        assert field in m, f"missing {field}"
