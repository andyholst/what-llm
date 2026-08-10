"""Crawler for trending Hugging Face models -> strict-contract per-model JSON files.

Design (verified against the live API + skeptic-reviewed):
  - GET /api/models?sort=trendingScore&limit=100 with repeated
    expand=config&expand=safetensors&expand=gguf; paginate via the Link cursor header.
  - parameters_b from safetensors.total (or gguf.total — both are PARAMETER COUNTS,
    never bytes); dense/MoE from config.model_type / num_experts / architectures
    (model_type is authoritative — DeepseekV3ForCausalLM has no 'Moe' substring).
  - GGUF repos: real per-quant file sizes from the tree endpoint; non-GGUF models get
    synthesized quants from the estimator's bytes/param table.
  - VRAM + hardware flags via whatllm.estimator; schema gate before any write.
  - Rate limiting (0.6 s between calls, retry-after honored on 429) and a checkpoint in
    data/state.json so interrupted runs resume without re-fetching completed models.

CLI: python -m whatllm.crawl_models --limit 150 [--filter text-generation|gguf|none]
                                  [--out models] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests

from whatllm import artifacts, estimator, profile, servers

log = logging.getLogger("whatllm.crawl")

API = "https://huggingface.co/api"
PAGE_SIZE = 100
RATE_DELAY_S = 0.6          # HF quota ~500 req / 300 s unauthenticated
MAX_RETRIES = 3
QUANT_RE = re.compile(
    r"-(Q\d+_K(?:_\w+)?|Q8_0|Q6_K(?:_L)?|IQ\d(?:_\w+)?)(?:-\d+-of-\d+)?\.gguf$", re.I)

# licenses that forbid commercial use (curated; extend as needed)
NC_LICENSES = {
    "cc-by-nc-4.0", "cc-by-nc-3.0", "cc-by-nc-2.5", "cc-by-nc-2.0", "cc-by-nc-1.0",
    "cc-by-nc-sa-4.0", "cc-by-nc-sa-3.0", "cc-by-nc-nd-4.0", "cc-by-nc-nd-3.0",
    "nc", "non-commercial", "odc-by-1.0" + "-nc",  # no-op safety: exact ids only below
}
NC_LICENSES.discard("odc-by-1.0-nc")

# licenses that ALLOW commercial use but with conditions (shown as a limitation note)
CONDITIONAL_LICENSES = {"llama3.1", "llama3.2", "llama3.3", "gemma", "qwen", "deepseek"}

# config keys that mark a model as MoE (DeepSeek-V3 uses n_routed_experts and has no
# 'moe' anywhere in model_type/architectures — verified against the live API)
EXPERT_KEYS = ("num_experts", "num_local_experts", "n_routed_experts", "n_shared_experts",
               "moe_intermediate_size", "num_experts_per_tok", "n_experts")

FOCUS_PIPELINES = {"text-generation", "image-text-to-text", "text-to-text"}

LANG_RE = re.compile(r"^[a-z]{2,3}(-[A-Z]{2})?$")
CUTOFF_RE = re.compile(
    r"(?:knowledge|training data|cutoff)[^.]{0,90}?((?:19|20)\d{2})[-/.](\d{1,2})", re.I)


def commercial_ok(license_name: str) -> bool:
    return license_name.lower() not in NC_LICENSES


def detect_model_type(model_id: str, base_model, tags: list[str] | None,
                      pipeline_tag: str | None) -> str:
    """base/instruct/chat/reasoner/vision from cardData.base_model (a LIST when present),
    id-suffix heuristics, and tags — top-level base_model is null on BOTH variants."""
    tags = tags or []
    mid = model_id.lower()
    if "vision" in mid or "-vl" in mid or mid.endswith("vl") or pipeline_tag == "image-text-to-text":
        return "vision"
    if any(k in mid for k in ("reasoner", "thinking", "-r1", "-r2", "reasoning")):
        return "reasoner"
    if base_model:  # instruct/chat lineage exists
        if "conversational" in tags or any(k in mid for k in ("-chat", "-it", "-instruct")):
            return "chat"
        return "instruct"
    return "base"


def detect_languages(tags: list[str] | None) -> list[str]:
    return sorted({t for t in (tags or []) if LANG_RE.fullmatch(t)})


def detect_knowledge_cutoff(readme_text: str | None) -> str | None:
    if not readme_text:
        return None
    m = CUTOFF_RE.search(readme_text)
    if not m:
        return None
    try:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    except ValueError:
        return None


class HFError(RuntimeError):
    pass


def http_get_json(url: str, params: dict | None = None, timeout: float = 30.0) -> tuple[dict | list, str | None]:
    """GET url -> (json, next_cursor_or_None). Single injectable HTTP entry (tests patch this)."""
    for attempt in range(MAX_RETRIES):
        resp = requests.get(url, params=params, timeout=timeout)
        if resp.status_code == 429:
            retry = float(resp.headers.get("Retry-After", "5"))
            log.warning("rate limited: sleeping %.1fs", retry)
            time.sleep(retry)
            continue
        if resp.status_code >= 400:
            raise HFError(f"HTTP {resp.status_code} for {url}: {resp.text[:200]}")
        break
    cursor = None
    link = resp.headers.get("Link", "")
    m = re.search(r"<([^>]*cursor=[^>]*)>;\s*rel=\"next\"", link)
    if m:
        cursor = m.group(1)
    return resp.json(), cursor


def http_get_text(url: str, timeout: float = 30.0) -> str | None:
    """GET url -> raw text, or None on 4xx/5xx (gated/404). Injectable for tests."""
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.RequestException:
        return None
    if resp.status_code >= 400:
        return None
    return resp.text


def next_cursor_url(cursor: str) -> str:
    return cursor if cursor.startswith("http") else f"{API}{cursor}"


class Crawler:
    def __init__(self, limit: int = 150, focus: str = "text-generation",
                 out_dir: str = "models", state_file: str = "data/state.json",
                 dry_run: bool = False):
        self.limit = limit
        self.focus = focus
        self.out_dir = Path(out_dir)
        self.state_file = Path(state_file)
        self.dry_run = dry_run
        self.completed: set[str] = set()
        self.models: list[dict] = []

    # ---- checkpoint ----
    def load_state(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                self.completed = set(data.get("completed", []))
                log.info("resume: %d models already completed", len(self.completed))
            except (json.JSONDecodeError, OSError):
                log.warning("state file unreadable; starting fresh")

    def save_state(self):
        if self.dry_run:
            return
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"completed": sorted(self.completed)}, indent=2), encoding="utf-8")
        tmp.replace(self.state_file)

    # ---- fetch ----
    def fetch_trending(self) -> list[dict]:
        """Page through the trending list; returns raw list entries.

        NOTE: the list endpoint DROPS pipeline_tag/tags when expand= is passed, so the
        list is fetched PLAIN (for filtering) and details are fetched per model.
        """
        collected: list[dict] = []
        cursor: str | None = None
        while len(collected) < self.limit:
            params: dict = {"sort": "trendingScore", "limit": min(PAGE_SIZE, self.limit - len(collected))}
            url = next_cursor_url(cursor) if cursor else f"{API}/models"
            page, cursor = http_get_json(url, params=params if not cursor else None)
            if not isinstance(page, list) or not page:
                break
            collected.extend(page)
            log.info("page: %d models (total %d)", len(page), len(collected))
            if not cursor:
                break
            time.sleep(RATE_DELAY_S)
        return collected[: self.limit]

    @staticmethod
    def fetch_detail(model_id: str) -> dict:
        """Full metadata for one model: config, safetensors, gguf, tags (with expand)."""
        detail, _ = http_get_json(
            f"{API}/models/{model_id}",
            params={"expand": ["config", "safetensors", "gguf", "tags", "cardData", "evalResults"]},
        )
        if not isinstance(detail, dict) or not detail.get("id"):
            raise HFError(f"bad detail response for {model_id}")
        return detail

    def _keep(self, raw: dict) -> bool:
        if self.focus == "none":
            return True
        tags = raw.get("tags") or []
        pipeline = raw.get("pipeline_tag") or ""
        if "gguf" in tags:
            return True
        if self.focus == "gguf":
            return False
        return pipeline in FOCUS_PIPELINES

    # ---- extraction ----
    @staticmethod
    def extract(raw: dict) -> dict | None:
        """One raw list entry (with config/safetensors/gguf expands) -> contract dict or None."""
        model_id = raw.get("id")
        if not model_id:
            return None
        config = raw.get("config") or {}
        safetensors = raw.get("safetensors") or {}
        gguf = raw.get("gguf") or {}

        total = None
        if safetensors:
            total = safetensors.get("total")
        if total is None and gguf:
            total = gguf.get("total")   # param COUNT (verified), not bytes
        if not total:
            log.info("skip %s: no parameter count", model_id)
            return None

        params_b = round(total / 1e9, 2)
        model_type = str(config.get("model_type") or "").lower()
        archs = [str(a).lower() for a in (config.get("architectures") or [])]
        has_expert_keys = any(k in config for k in EXPERT_KEYS)
        is_moe = ("moe" in model_type or any("moe" in a for a in archs) or has_expert_keys)

        return {
            "id": model_id,
            "name": raw.get("modelId") or model_id.split("/")[-1],
            "author": model_id.split("/")[0],
            "parameters_b": params_b,
            "architecture": "moe" if is_moe else "dense",
            "pipeline_tag": raw.get("pipeline_tag") or "text-generation",
            "hf_url": f"https://huggingface.co/{model_id}",
            "trending_score": raw.get("trendingScore") or 0,
            "downloads": raw.get("downloads") or 0,
            "quants": [],   # filled by build_quants
            "hardware": {},  # filled after quants
            "last_updated": date.today().isoformat(),
        }

    def build_quants(self, model: dict, raw: dict) -> None:
        """Real GGUF sizes from the tree endpoint when available, else synthesized."""
        tags = raw.get("tags") or []
        real: list[dict] = []
        if "gguf" in tags:
            try:
                tree, _ = http_get_json(
                    f"{API}/models/{model['id']}/tree/main",
                    params={"recursive": "true", "expand": "false"},
                )
            except HFError as exc:
                log.warning("tree fetch failed for %s: %s", model["id"], exc)
                tree = []
            per_dir: dict[str, int] = {}
            if isinstance(tree, list):
                for entry in tree:
                    path = entry.get("path", "")
                    if entry.get("type") != "file" or not path.endswith(".gguf"):
                        continue
                    name = path.split("/")[-1]
                    m = QUANT_RE.search(name)
                    if not m:
                        continue
                    key = path.split("/")[0] if "/" in path else m.group(1)
                    per_dir[key] = per_dir.get(key, 0) + entry.get("size", 0)
            for name, size_bytes in sorted(per_dir.items(), key=lambda kv: kv[1]):
                real.append(estimator.quant_from_file(name, size_bytes))
            real = real[:8]
        model["quants"] = real if real else estimator.synthesize_quants(model["parameters_b"])
        model["hardware"] = estimator.hardware_flags(model["parameters_b"], model["quants"])

    # ---- metadata enrichment (extend-model-metadata, issues #8-#12, #15) ----
    def fetch_readme(self, model_id: str) -> str | None:
        """README text (None when gated/404). Gating is checked by the caller."""
        return http_get_text(f"https://huggingface.co/{model_id}/raw/main/README.md")

    def fetch_config_raw(self, model_id: str) -> dict | None:
        """Raw config.json (None when gated/404). expand=config only carries a curated subset."""
        try:
            cfg, _ = http_get_json(f"https://huggingface.co/{model_id}/raw/main/config.json")
        except HFError:
            return None
        return cfg if isinstance(cfg, dict) else None

    @staticmethod
    def _enrich(record: dict, detail: dict, readme_text: str | None,
                config: dict | None) -> None:
        """Add license/commercial_ok/context_window/model_type/languages/cutoff/
        benchmarks/profile to a contract record (all derived programmatically)."""
        card = detail.get("cardData") or {}
        tags = detail.get("tags") or []
        license_name = (card.get("license") or
                        next((t.split(":", 1)[1] for t in tags if t.startswith("license:")),
                             "unknown"))
        ctx = None
        if isinstance(config, dict):
            ctx = (config.get("max_position_embeddings") or config.get("n_positions"))
            if ctx is None and isinstance(config.get("sliding_window"), int):
                ctx = config["sliding_window"]
        gated = detail.get("gated") not in (False, None)
        base_model = card.get("base_model")  # LIST when present (skeptic C2/C4)
        model_type = detect_model_type(record["id"], base_model, tags,
                                       detail.get("pipeline_tag"))
        benchmarks = [
            {
                "dataset": (e.get("data") or {}).get("dataset", {}).get("id", "unknown"),
                "value": (e.get("data") or {}).get("value"),
                "verified": bool(e.get("verified")),
                "date": (e.get("data") or {}).get("date"),
                "source": ((e.get("data") or {}).get("source") or {}).get("name"),
            }
            for e in (detail.get("evalResults") or [])
        ]

        record["license"] = license_name
        record["commercial_ok"] = commercial_ok(license_name)
        record["context_window"] = ctx
        record["model_type"] = model_type
        record["languages"] = detect_languages(tags)
        record["knowledge_cutoff"] = detect_knowledge_cutoff(readme_text)
        record["benchmarks"] = benchmarks
        record["servers"] = servers.servers_for_model(record["quants"])
        record["profile"] = profile.build_profile(
            record["id"],
            readme_text=readme_text,
            family=profile.family_for(record["id"]),
            tags=tags,
            eval_entries=benchmarks,
            context_window=ctx,
            license_name=license_name,
            commercial_ok=record["commercial_ok"],
            model_type=model_type,
            gated=gated,
        )

    # ---- pipeline ----
    def run(self) -> list[dict]:
        self.load_state()
        raw_list = self.fetch_trending()
        log.info("fetched %d trending entries, applying focus filter=%s", len(raw_list), self.focus)
        kept = [r for r in raw_list if self._keep(r)]
        log.info("%d models pass the focus filter", len(kept))
        for raw in kept:
            model_id = raw.get("id")
            if model_id in self.completed:
                continue
            detail = self.fetch_detail(model_id)
            record = self.extract(detail)
            if record is None:
                continue
            self.build_quants(record, detail)
            readme_text = None
            config = None
            if detail.get("gated") in (False, None):
                readme_text = self.fetch_readme(model_id)
                time.sleep(RATE_DELAY_S)
                config = self.fetch_config_raw(model_id)
            self._enrich(record, detail, readme_text, config)
            errors = artifacts.validate_model(record)
            if errors:
                log.warning("skip %s: schema invalid: %s", model_id, errors[:2])
                continue
            self.models.append(record)
            if model_id:
                self.completed.add(model_id)
            self.save_state()
            time.sleep(RATE_DELAY_S)
        log.info("crawl complete: %d valid models", len(self.models))
        return self.models

    def emit(self) -> None:
        if self.dry_run or not self.models:
            log.info("dry-run: %d models would be written to %s", len(self.models), self.out_dir)
            return
        artifacts.emit_artifacts(self.models, self.out_dir)
        log.info("wrote %d model files + index artifacts to %s", len(self.models), self.out_dir)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="crawl_models",
        description="Fetch trending HF models and emit strict-contract JSON into models/.",
    )
    p.add_argument("--limit", type=int, default=150, help="max models to crawl (default 150)")
    p.add_argument("--filter", choices=["text-generation", "gguf", "none"],
                   default="text-generation", help="focus filter (default text-generation)")
    p.add_argument("--out", default="models", help="output directory (default models)")
    p.add_argument("--state", default="data/state.json", help="checkpoint file")
    p.add_argument("--dry-run", action="store_true", help="fetch + validate but do not write")
    p.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    crawler = Crawler(limit=args.limit, focus=args.filter, out_dir=args.out,
                      state_file=args.state, dry_run=args.dry_run)
    try:
        crawler.run()
        crawler.emit()
    except HFError as exc:
        log.error("crawl aborted: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
