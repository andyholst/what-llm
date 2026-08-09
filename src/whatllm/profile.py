"""Python-derived model profiles (extend-model-metadata, issue #7, #11).

Builds `profile {summary, best_for[], strengths[], weaknesses[], limitations[],
provenance[]}` for a model WITHOUT hand-written notes:

  1. README section mining  - org-specific headings normalized (## Limitations,
     ## Weaknesses, ## Highlights/Strengths, ## Intended Use(s), ## Model Overview)
  2. structured inference   - evalResults -> strength candidates; context window ->
     capability note; license -> limitation; gating -> limitation; base model -> note
  3. curated family fallback - deterministic per-family map used when the README is
     gated or absent; claims tagged `source: curated`

Every claim carries provenance {claim, source, confidence}. No network I/O here —
the crawler feeds us the README text and structured fields.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# use-case keyword mapping (README/tag text -> best_for candidates)
# ---------------------------------------------------------------------------
USE_CASE_KEYWORDS = {
    "coding": ["code", "coding", "program", "python", "javascript", "software",
               "developer", "function calling", "typescript", "github"],
    "reasoning": ["reason", "math", "logic", "solve", "thinking", "chain-of-thought",
                  "step-by-step", "scientific"],
    "chat": ["chat", "conversation", "assistant", "dialogue", "companion", "instruct"],
    "summarization": ["summar", "abstract", "condense", "notes"],
    "rag": ["retrieval", "rag", "embedding", "document", "knowledge base", "long context"],
    "agentic": ["agent", "tool use", "api calls", "tool calling"],
    "roleplay": ["roleplay", "character", "story", "creative writing", "fiction"],
    "translation": ["translat", "multilingual", "language model"],
}

# README heading (normalized) -> canonical slot
SECTION_SLOTS = {
    "limitations": ["limitations", "known limitations", "limitation", "what it cannot do"],
    "weaknesses": ["weaknesses", "weakness", "disadvantages", "drawbacks"],
    "strengths": ["strengths", "strength", "advantages", "highlights", "key features",
                  "capabilities", "model highlights"],
    "intended_use": ["intended use", "intended uses", "use cases", "use case", "usage",
                     "what is this", "what is this model", "model overview",
                     "introduction", "overview"],
}

HEADING_RE = re.compile(r"^#{1,4}\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*[-*•]\s+(.+?)\s*$")
LIST_RE = re.compile(r"^\s*\d+[.)]\s+(.+?)\s*$")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def split_sections(text: str | None) -> dict[str, list[str]]:
    """Mine a README body: {canonical_slot: [bullets]} (list/order-insensitive)."""
    if not text:
        return {}
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for ln in text.splitlines():
        m = HEADING_RE.match(ln)
        if m:
            current = _norm(m.group(1))
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(ln)

    out: dict[str, list[str]] = {}
    for heading, content in sections.items():
        for slot, aliases in SECTION_SLOTS.items():
            if any(heading == a or heading.startswith(a) for a in aliases):
                bullets = []
                for c in content:
                    b = BULLET_RE.match(c) or LIST_RE.match(c)
                    if b:
                        bullets.append(b.group(1).strip())
                if bullets:
                    out.setdefault(slot, []).extend(bullets)
    return out


def infer_use_cases(blob: str, tags: list[str] | None = None) -> list[str]:
    """Keyword-scan README/tags for best_for candidates (dedup, order stable)."""
    text = (blob or "").lower()
    found: list[str] = []
    for uc, kws in USE_CASE_KEYWORDS.items():
        if any(kw in text for kw in kws):
            found.append(uc)
    if tags:
        if "conversational" in tags and "chat" not in found:
            found.append("chat")
        if "text-generation-inference" in tags and "agentic" not in found:
            found.append("agentic")
    return found


# ---------------------------------------------------------------------------
# curated family fallback (used when README gated/absent; claims tagged curated)
# ---------------------------------------------------------------------------
CURATED_FAMILIES: dict[str, dict] = {
    "qwen": {
        "summary": "Qwen: strong general-purpose chat, reasoning and coding; long context; multilingual.",
        "best_for": ["chat", "reasoning", "coding", "rag"],
        "strengths": ["Strong instruction following and general chat", "Good multilingual support",
                      "Long context windows (often 32k+)"],
        "weaknesses": ["Heavier than comparable 7-8B models for the same quality", "Some variants need specific tooling for best results"],
        "limitations": ["Knowledge cutoff varies by variant (see model card)", "Coder/reasoner variants are specialized"],
    },
    "llama": {
        "summary": "Llama: solid general-purpose chat with broad ecosystem support (llama.cpp, vLLM).",
        "best_for": ["chat", "rag", "agentic"],
        "strengths": ["Excellent ecosystem and quantization support", "Well-tuned instruct variants"],
        "weaknesses": ["Benchmarks often matched by newer smaller models", "Gated card — README not anonymous-accessible"],
        "limitations": ["Llama community license: commercial use ok but MAU >700M needs Meta approval",
                        "Gated model card (login required for files)"],
    },
    "mistral": {
        "summary": "Mistral: efficient chat with strong reasoning-per-parameter; Apache/MIT friendly.",
        "best_for": ["chat", "reasoning", "rag"],
        "strengths": ["Strong quality per parameter", "Permissive licenses on many variants"],
        "weaknesses": ["Smaller context on some variants (8k)", "Sliding-window attention quirks on some tools"],
        "limitations": [],
    },
    "mixtral": {
        "summary": "Mixtral: sparse MoE — near-larger-model quality at lower active-parameter cost.",
        "best_for": ["chat", "reasoning"],
        "strengths": ["MoE efficiency: strong quality per active parameter", "Good multilingual support"],
        "weaknesses": ["High TOTAL parameter count — needs lots of VRAM/RAM (all experts resident)"],
        "limitations": ["32GB-class machines are borderline at Q4 (see hardware flags)"],
    },
    "deepseek": {
        "summary": "DeepSeek: frontier-scale reasoning and coding MoE models.",
        "best_for": ["reasoning", "coding"],
        "strengths": ["Frontier reasoning and math", "MoE design keeps active params low"],
        "weaknesses": ["Very large total parameter count — datacenter class", "Specialized tooling for some variants"],
        "limitations": ["Consumer GPUs rarely fit even the smallest quants", "Gated on some variants"],
    },
    "phi": {
        "summary": "Phi: compact models ideal for edge/mobile and constrained hardware.",
        "best_for": ["chat", "reasoning", "mobile"],
        "strengths": ["Small footprint (3-4B) fits phones and low-end GPUs", "Surprisingly strong reasoning for size"],
        "weaknesses": ["Smaller knowledge base", "License terms vary by version (MIT/other)"],
        "limitations": [],
    },
    "gemma": {
        "summary": "Gemma: open Google models, strong at general chat; multilingual on newer versions.",
        "best_for": ["chat", "reasoning"],
        "strengths": ["Good general chat quality", "Multilingual in 3.x versions"],
        "weaknesses": ["Gated card on some versions", "Smaller ecosystem than Llama/Qwen"],
        "limitations": ["Google license terms apply"],
    },
    "kimi": {
        "summary": "Kimi/Moonshot: very large frontier MoE with strong reasoning.",
        "best_for": ["reasoning", "chat"],
        "strengths": ["Frontier reasoning at huge scale"],
        "weaknesses": ["Extreme parameter count — server only"],
        "limitations": ["No consumer hardware fits (see hardware flags)"],
    },
    "liquid": {
        "summary": "Liquid/LFM: small efficient models tuned for local reasoning.",
        "best_for": ["reasoning", "chat"],
        "strengths": ["Good reasoning per parameter", "Small sizes run locally"],
        "weaknesses": ["Smaller knowledge base"],
        "limitations": [],
    },
}

# GGUF/quant mirror orgs MUST inherit the UPSTREAM model's family profile — the id
# itself (e.g. "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF") carries the family name.
FAMILY_KEYWORDS = [
    ("deepseek", "deepseek"),
    ("qwen", "qwen"),
    ("llama", "llama"),
    ("mixtral", "mixtral"),
    ("mistral", "mistral"),
    ("phi", "phi"),
    ("gemma", "gemma"),
    ("kimi", "kimi"),
    ("liquid", "liquid"),
]


def family_for(model_id: str) -> str | None:
    """Map a model id to a curated family key by searching the WHOLE id.

    Org-prefix matching is deliberately avoided: GGUF mirrors (bartowski/, unsloth/,
    DavidAU/, ...) are quantization orgs, NOT model families — their profiles must
    inherit the upstream family (bartowski/Meta-Llama-... -> llama, unsloth/
    DeepSeek-... -> deepseek). Verified by tests/test_profile.py.
    """
    mid = model_id.lower()
    for keyword, fam in FAMILY_KEYWORDS:
        if keyword in mid:
            return fam
    return None


# ---------------------------------------------------------------------------
# profile assembly
# ---------------------------------------------------------------------------
def build_profile(
    model_id: str,
    *,
    readme_text: str | None = None,
    family: str | None = None,
    tags: list[str] | None = None,
    eval_entries: list[dict] | None = None,
    context_window: int | None = None,
    license_name: str | None = None,
    commercial_ok: bool | None = None,
    model_type: str | None = None,
    gated: bool = False,
) -> dict:
    """Assemble the full profile with per-claim provenance."""
    mined = split_sections(readme_text)
    cur = CURATED_FAMILIES.get(family or "") or {}

    strengths: list[str] = []
    weaknesses: list[str] = []
    limitations: list[str] = []
    provenance: list[dict] = []

    def add(slot: str, claim: str, source: str, confidence: str = "high") -> None:
        target = {"strengths": strengths, "weaknesses": weaknesses,
                  "limitations": limitations}[slot]
        target.append(claim)
        provenance.append({"claim": claim, "source": source, "confidence": confidence})

    # 1) README-mined claims
    for c in mined.get("strengths", []):
        add("strengths", c, "readme")
    for c in mined.get("weaknesses", []):
        add("weaknesses", c, "readme")
    for c in mined.get("limitations", []):
        add("limitations", c, "readme")

    # 2) structured inference
    for e in eval_entries or []:
        dataset = e.get("dataset") or "unknown benchmark"
        value = e.get("value")
        mark = "verified" if e.get("verified") else "unverified community result"
        if value is not None:
            add("strengths", f"{dataset}: {value} ({mark})", "evals", "medium")
    if context_window:
        add("strengths", f"Supports up to {context_window:,} tokens of context", "config")
        if context_window < 8192:
            add("limitations", f"Short context window ({context_window:,} tokens)", "config", "medium")
    if commercial_ok is False and license_name:
        add("limitations", f"Non-commercial license ({license_name}) — check before shipping", "tags")
    if gated:
        add("limitations", "Model card is gated — README not accessible to anonymous crawls", "config", "medium")
    if model_type == "base":
        add("limitations", "Base (pre-instruct) model — use the instruct/chat variant for conversation", "curated", "high")

    # 3) curated family claims
    for c in cur.get("strengths", []):
        if c not in strengths:
            add("strengths", c, "curated", "medium")
    for c in cur.get("weaknesses", []):
        if c not in weaknesses:
            add("weaknesses", c, "curated", "medium")
    for c in cur.get("limitations", []):
        if c not in limitations:
            add("limitations", c, "curated", "medium")

    # best_for: curated + README keyword scan
    best_for = list(cur.get("best_for", []))
    for uc in infer_use_cases(readme_text or "", tags):
        if uc not in best_for:
            best_for.append(uc)
    if not best_for:
        best_for = ["chat"]  # conservative default for text-generation models

    summary = cur.get("summary") or (
        f"{family or model_id}: see strengths/weaknesses for what it is good at "
        f"and where it falls short."
    )

    return {
        "summary": summary,
        "best_for": best_for[:6],
        "strengths": strengths,
        "weaknesses": weaknesses,
        "limitations": limitations,
        "provenance": provenance,
    }
