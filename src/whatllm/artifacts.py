"""Artifact emission + schema validation helpers for the what-llm pipeline.

Shared by crawl_models.py and make_samples.py:
  - models/<sanitized-id>.json    one strict-contract file per model
  - models/index.json             summary list (card fields)
  - models/index.js               window.MODELS_INDEX (script-tag, file://-safe)
  - models/bundle.js              window.MODELS_BUNDLE (id -> model, file://-safe)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "model.schema.json"

SUMMARY_FIELDS = [
    "id", "name", "author", "parameters_b", "architecture",
    "pipeline_tag", "trending_score", "downloads", "est_vram_gb",
    "model_type", "commercial_ok", "license", "best_for", "servers",
]


def _summary_entry(model: dict) -> dict:
    """Card-row summary: est_vram derived from the recommended quant; the rest of the
    v3 fields (model_type/commercial_ok/license/best_for) drive the frontend filters."""
    entry = {k: model[k] for k in SUMMARY_FIELDS if k in model and k != "best_for"}
    entry["est_vram_gb"] = (
        model["quants"][0]["estimated_vram_gb"] if model.get("quants") else None
    )
    entry["best_for"] = (model.get("profile") or {}).get("best_for", [])
    return entry


def sanitize_id(model_id: str) -> str:
    """'author/model' -> 'author__model' (safe filename)."""
    return model_id.replace("/", "__")


def _escaped_json(obj) -> str:
    """JSON that is also safe to embed in a <script> tag (escapes '</')."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_model(record: dict) -> list[str]:
    """Return list of schema errors (empty = valid)."""
    try:
        jsonschema.validate(record, load_schema())
        return []
    except jsonschema.ValidationError as exc:
        return [exc.message]


def write_model_file(model: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{sanitize_id(model['id'])}.json"
    path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def emit_artifacts(models: list[dict], out_dir: Path, crawled_at: str | None = None) -> None:
    """Write per-model files + index.json + index.js + bundle.js + meta.json for `models`."""
    from datetime import date as _date

    out_dir.mkdir(parents=True, exist_ok=True)
    for model in models:
        write_model_file(model, out_dir)

    summary = [_summary_entry(m) for m in models]
    meta = {"crawled_at": crawled_at or _date.today().isoformat(), "count": len(models)}
    (out_dir / "index.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "index.js").write_text(
        "window.MODELS_META = " + _escaped_json(meta) + ";\n"
        "window.MODELS_INDEX = " + _escaped_json(summary) + ";\n",
        encoding="utf-8",
    )
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "bundle.js").write_text(
        "window.MODELS_BUNDLE = " + _escaped_json({m["id"]: m for m in models}) + ";\n",
        encoding="utf-8",
    )
