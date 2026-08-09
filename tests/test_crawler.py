"""Hermetic crawler tests — every HTTP call is mocked via http_get_json (no network).

Covers base-change tasks 5.1-5.12: pagination/limit, focus filter, metadata extraction
(dense/MoE incl. the deepseek_v3 model_type case), parameter skip, GGUF real-size
discovery vs synthesized fallback, schema gate, checkpoint resume, CLI behavior.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from whatllm import crawl_models as cm

# ---------------- fixtures ----------------
def raw_entry(model_id="Qwen/Qwen3-8B", pipeline="text-generation", tags=None,
              total=8_190_735_360, model_type="qwen3", archs=("Qwen3ForCausalLM",),
              num_experts=None, trending=100, downloads=5000):
    cfg = {"model_type": model_type, "architectures": list(archs)}
    if num_experts is not None:
        cfg["num_experts"] = num_experts
    return {
        "id": model_id, "modelId": model_id, "pipeline_tag": pipeline,
        "tags": tags or [], "trendingScore": trending, "downloads": downloads,
        "config": cfg,
        "safetensors": {"total": total} if total else {},
        "gguf": {},
    }


def tree_entry(path: str, size: int):
    return {"type": "file", "path": path, "size": size}


class FakeAPI:
    """Scriptable stand-in for http_get_json(url, params)."""

    def __init__(self):
        self.calls: list[tuple[str, dict | None]] = []
        self.pages: list[list[dict]] = []
        self.tree: dict[str, list] = {}
        self.details: dict[str, dict] = {}
        self.cursor_next = True

    def __call__(self, url, params=None, timeout=30.0):
        self.calls.append((url, params))
        if "/tree/main" in url:
            model_id = url.split("/api/models/")[1].split("/tree")[0]
            return self.tree.get(model_id, []), None
        if url.startswith("https://huggingface.co/api/models/"):
            # detail call: .../api/models/<author>/<name> (params go to requests, not the url)
            model_id = url.split("/api/models/")[1]
            return self.details.get(model_id, {}), None
        if "cursor=" in url:
            return (self.pages[1] if len(self.pages) > 1 else []), None
        return (self.pages[0] if self.pages else []), ("https://x?cursor=abc" if self.cursor_next else None)


def make_crawler(fake: FakeAPI, **kw):
    c = cm.Crawler(**kw)
    cm_http = cm.http_get_json
    cm.http_get_json = fake
    try:
        return c
    finally:
        pass


@pytest.fixture
def fake(monkeypatch):
    f = FakeAPI()
    monkeypatch.setattr(cm, "http_get_json", f)
    return f


# ---------------- 5.1 pagination + limit ----------------
def test_pagination_stops_at_limit(fake):
    fake.pages = [[raw_entry(f"a/m{i}") for i in range(50)],
                  [raw_entry(f"b/m{i}") for i in range(50)]]
    c = cm.Crawler(limit=80, focus="none", dry_run=True)
    collected = c.fetch_trending()
    assert len(collected) == 80
    assert len(fake.calls) == 2


def test_no_next_cursor_stops(fake):
    fake.pages = [[raw_entry("a/m1")]]
    fake.cursor_next = False
    c = cm.Crawler(limit=500, focus="none", dry_run=True)
    assert len(c.fetch_trending()) == 1


# ---------------- 5.2/5.3 extraction ----------------
def test_extract_dense(fake):
    raw = raw_entry()
    m = cm.Crawler.extract(raw)
    assert m["id"] == "Qwen/Qwen3-8B"
    assert m["parameters_b"] == 8.19
    assert m["architecture"] == "dense"
    assert m["pipeline_tag"] == "text-generation"


def test_extract_moe_qwen3_moe(fake):
    raw = raw_entry(model_type="qwen3_moe", archs=("Qwen3MoeForCausalLM",),
                    num_experts=128, total=30_532_122_624)
    m = cm.Crawler.extract(raw)
    assert m["architecture"] == "moe"
    assert m["parameters_b"] == 30.53


def test_extract_moe_deepseek_v3_no_moe_in_arch(fake):
    # DeepseekV3ForCausalLM + model_type deepseek_v3 contain NO 'moe' anywhere —
    # the num_experts/n_routed_experts config keys are the authoritative signal
    raw = raw_entry(model_type="deepseek_v3", archs=("DeepseekV3ForCausalLM",),
                    total=671_000_000_000, num_experts=256)
    m = cm.Crawler.extract(raw)
    assert m["architecture"] == "moe"


def test_extract_moe_deepseek_v3_via_n_routed_experts(fake):
    cfg_raw = raw_entry(model_type="deepseek_v3", archs=("DeepseekV3ForCausalLM",),
                        total=671_000_000_000)
    cfg_raw["config"]["n_routed_experts"] = 256
    m = cm.Crawler.extract(cfg_raw)
    assert m["architecture"] == "moe"


def test_extract_skip_when_no_params(fake, caplog):
    raw = raw_entry(total=None)
    raw["safetensors"] = {}
    assert cm.Crawler.extract(raw) is None


# ---------------- focus filter ----------------
def test_focus_keeps_gguf_and_text_gen(fake):
    gguf = raw_entry("u/v-GGUF", tags=["gguf"], pipeline="video-to-video")
    text = raw_entry("q/r", pipeline="text-generation")
    video = raw_entry("s/t", pipeline="text-to-video")
    fake.pages = [[gguf, text, video]]
    c = cm.Crawler(limit=10, focus="text-generation", dry_run=True)
    assert [r["id"] for r in c.fetch_trending() if c._keep(r)] == ["u/v-GGUF", "q/r"]


# ---------------- 5.3 GGUF discovery ----------------
def test_gguf_real_sizes_from_split_files(fake):
    raw = raw_entry("bartowski/Meta-Llama-3.1-8B-Instruct-GGUF", tags=["gguf"])
    fake.tree["bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"] = [
        tree_entry("Q4_K_M/Meta-Llama-3.1-8B-Instruct-Q4_K_M-00001-of-00002.gguf", 2_460_369_616),
        tree_entry("Q4_K_M/Meta-Llama-3.1-8B-Instruct-Q4_K_M-00002-of-00002.gguf", 2_460_369_616),
        tree_entry("Q8_0/Meta-Llama-3.1-8B-Instruct-Q8_0.gguf", 8_540_000_000),
        tree_entry("README.md", 100),
    ]
    m = cm.Crawler.extract(raw)
    c = cm.Crawler(limit=5, dry_run=True)
    c.build_quants(m, raw)
    names = [q["name"] for q in m["quants"]]
    assert names == ["Q4_K_M", "Q8_0"]
    assert m["quants"][0]["size_gb"] == 4.92  # split files summed, decimal GB
    assert m["hardware"]["nvidia"]["8gb"] is True


def test_non_gguf_synthesizes_quants(fake):
    raw = raw_entry()
    m = cm.Crawler.extract(raw)
    c = cm.Crawler(limit=5, dry_run=True)
    c.build_quants(m, raw)
    assert [q["name"] for q in m["quants"]] == ["Q4_K_M", "Q5_K_M", "Q8_0", "FP16"]
    assert m["quants"][0]["size_gb"] == round(8.19 * 0.612, 2)


# ---------------- 5.5 schema gate ----------------
def test_invalid_record_skipped(fake, monkeypatch, caplog):
    fake.pages = [[raw_entry("a/ok")]]
    fake.details["a/ok"] = raw_entry("a/ok")
    monkeypatch.setattr(cm.artifacts, "validate_model", lambda rec: ["boom"])
    c = cm.Crawler(limit=5, focus="none", dry_run=True)
    models = c.run()
    assert models == []


# ---------------- 5.6 resume/checkpoint ----------------
def test_resume_skips_completed(fake, tmp_path):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"completed": ["a/done"]}), encoding="utf-8")
    fake.pages = [[raw_entry("a/done"), raw_entry("b/new")]]
    fake.details["a/done"] = raw_entry("a/done")
    fake.details["b/new"] = raw_entry("b/new")
    c = cm.Crawler(limit=5, focus="none", dry_run=False, state_file=str(state))
    models = c.run()
    assert [m["id"] for m in models] == ["b/new"]
    data = json.loads(state.read_text(encoding="utf-8"))
    assert "b/new" in data["completed"]


# ---------------- 5.11/5.12 CLI ----------------
def test_cli_help(capsys):
    with pytest.raises(SystemExit) as e:
        cm.main(["--help"])
    assert e.value.code == 0
    assert "--limit" in capsys.readouterr().out


def test_cli_dry_run_no_writes(fake, tmp_path, monkeypatch):
    fake.pages = [[raw_entry("a/m1")]]
    fake.details["a/m1"] = raw_entry("a/m1")
    out = tmp_path / "out"
    rc = cm.main(["--limit", "1", "--filter", "none", "--dry-run", "--out", str(out),
                  "--state", str(tmp_path / "s.json")])
    assert rc == 0
    assert not out.exists()


def test_cli_real_run_writes_artifacts(fake, tmp_path):
    fake.pages = [[raw_entry("a/m1", downloads=7)]]
    fake.details["a/m1"] = raw_entry("a/m1", downloads=7)
    fake.cursor_next = False
    out = tmp_path / "models"
    rc = cm.main(["--limit", "1", "--filter", "none", "--out", str(out),
                  "--state", str(tmp_path / "s.json")])
    assert rc == 0
    assert (out / "a__m1.json").exists()
    assert (out / "index.json").exists()
    assert (out / "index.js").exists()
    assert (out / "bundle.js").exists()
    record = json.loads((out / "a__m1.json").read_text(encoding="utf-8"))
    assert record["id"] == "a/m1"
    assert record["hardware"]["dgx"]["640gb"] is True
